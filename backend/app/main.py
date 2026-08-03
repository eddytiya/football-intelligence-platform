import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dashboard import (
    router as dashboard_router,
)

from app.api.match import (
    router as match_router,
)

from app.api.prediction import (
    router as prediction_router,
)
from app.api.prediction_analytics import (
    router as prediction_analytics_router,
)
from app.api.prediction_evaluation import (
    router as prediction_evaluation_router,
)
from app.api.competition import (
    router as competition_router,
)
from app.api.team import (
    router as team_router,
)
from app.api.auth import router as auth_router
from app.api.notifications import router as notifications_router
from app.api.news import router as news_router
from app.api.players import router as players_router
from app.core.config import settings
from app.db.database import engine
from app.models.match import Match
from app.models.user import Notification, User, UserFavourite, UserWatchlist
from app.db.session import SessionLocal
from app.services.etl.live_score_sync import FutureFixtureSync, LiveScoreSync
from app.services.etl.api_football_squad_sync import APIFootballSquadSync
from app.services.notifications.email_sender import send_email
from app.services.notifications.notification_service import create_notification


logger = logging.getLogger(__name__)


async def live_score_sync_loop():
    """Refresh provider scores at a conservative, free-tier-safe interval."""
    interval_seconds = max(settings.LIVE_SCORE_SYNC_INTERVAL_MINUTES, 5) * 60
    while True:
        db = SessionLocal()
        try:
            result = await asyncio.to_thread(LiveScoreSync(db).run)
            logger.info("Live score sync complete: %s", result)
        except Exception:
            logger.exception("Live score sync failed")
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)


async def future_fixture_sync_loop():
    """Import announced future fixtures daily; separate from frequent score polling."""
    interval_seconds = max(settings.FUTURE_FIXTURE_SYNC_INTERVAL_HOURS, 1) * 60 * 60
    while True:
        db = SessionLocal()
        try:
            result = await asyncio.to_thread(FutureFixtureSync(db).run)
            logger.info("Future fixture sync complete: %s", result)
        except Exception:
            logger.exception("Future fixture sync failed")
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)


async def api_football_squad_sync_loop():
    """Refresh a free-tier-safe rotating squad batch every 26 hours."""
    while True:
        db = SessionLocal()
        try:
            result = await asyncio.to_thread(
                APIFootballSquadSync(db).run_batch,
                limit=settings.API_FOOTBALL_SQUAD_SYNC_DAILY_LIMIT,
            )
            logger.info("API-Football squad sync complete: %s", result)
        except Exception:
            logger.exception("API-Football squad sync failed")
        finally:
            db.close()
        await asyncio.sleep(max(settings.API_FOOTBALL_SQUAD_SYNC_INTERVAL_HOURS, 1) * 60 * 60)


def _run_watchlist_notification_sweep(db) -> dict:
    """Create kick-off-reminder and result notifications for watchlisted fixtures."""

    created = 0
    now = datetime.utcnow()
    rows = (
        db.query(UserWatchlist, Match, User)
        .join(Match, Match.id == UserWatchlist.match_id)
        .join(User, User.id == UserWatchlist.user_id)
        .filter(Match.status.in_(["SCHEDULED", "FINISHED"]))
        .all()
    )
    for watchlist_entry, match, user in rows:
        home = match.home_team.name if match.home_team else "Home team"
        away = match.away_team.name if match.away_team else "Away team"
        fixture = f"{home} vs {away}"

        if match.status == "SCHEDULED" and match.utc_date is not None:
            minutes_until_kickoff = (match.utc_date - now).total_seconds() / 60
            if 0 <= minutes_until_kickoff <= watchlist_entry.reminder_minutes:
                notification = create_notification(
                    db, user.id, "kickoff_reminder",
                    title=f"Kick-off soon: {fixture}",
                    body=f"{fixture} kicks off at {match.utc_date.strftime('%H:%M UTC')}.",
                    match_id=match.id,
                )
                if notification:
                    created += 1
                    send_email(user.email, notification.title, notification.body)

        elif match.status == "FINISHED":
            score = f"{match.home_score if match.home_score is not None else '-'}-{match.away_score if match.away_score is not None else '-'}"
            notification = create_notification(
                db, user.id, "result",
                title=f"Full time: {fixture}",
                body=f"{fixture} finished {score}.",
                match_id=match.id,
            )
            if notification:
                created += 1
                send_email(user.email, notification.title, notification.body)

    return {"notifications_created": created}


async def watchlist_notification_loop():
    """Notify users of kick-offs and results for their watchlisted fixtures."""
    interval_seconds = max(settings.WATCHLIST_NOTIFICATION_INTERVAL_MINUTES, 1) * 60
    while True:
        db = SessionLocal()
        try:
            result = await asyncio.to_thread(_run_watchlist_notification_sweep, db)
            logger.info("Watchlist notification sweep complete: %s", result)
        except Exception:
            logger.exception("Watchlist notification sweep failed")
        finally:
            db.close()
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # The existing project does not use Alembic migrations at runtime. Create
    # only the new account table safely if it is not already present.
    User.__table__.create(bind=engine, checkfirst=True)
    UserFavourite.__table__.create(bind=engine, checkfirst=True)
    UserWatchlist.__table__.create(bind=engine, checkfirst=True)
    Notification.__table__.create(bind=engine, checkfirst=True)
    task = None
    if settings.LIVE_SCORE_SYNC_ENABLED:
        task = asyncio.create_task(live_score_sync_loop())
        fixture_task = asyncio.create_task(future_fixture_sync_loop())
    else:
        fixture_task = None
    squad_task = asyncio.create_task(api_football_squad_sync_loop()) if (
        settings.API_FOOTBALL_SQUAD_SYNC_ENABLED and settings.API_FOOTBALL_KEY
    ) else None
    notification_task = asyncio.create_task(watchlist_notification_loop())
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    if fixture_task:
        fixture_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await fixture_task
    if squad_task:
        squad_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await squad_task
    notification_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await notification_task
app = FastAPI(
    title="Football Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# ==========================================================
# CORS Configuration
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# API Routers
# ==========================================================

app.include_router(prediction_router)
app.include_router(prediction_evaluation_router)
app.include_router(prediction_analytics_router)
app.include_router(dashboard_router)
app.include_router(match_router)
app.include_router(competition_router)
app.include_router(team_router)
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(news_router)
app.include_router(players_router)

# ==========================================================
# Root Endpoint
# ==========================================================

@app.get("/")
def root():
    return {
        "message": "Football Intelligence Platform API is running."
    }
