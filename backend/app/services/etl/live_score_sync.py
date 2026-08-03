"""Small, free-tier-friendly score refresh for matches already in our database."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.match_repository import MatchRepository
from app.services.football_api import FootballAPIClient
from app.services.matching.match_mapper import MatchMapper


class LiveScoreSync:
    """Refresh statuses and full-time scores without importing new fixture data."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MatchRepository(db)
        self.api_client = FootballAPIClient()

    def run(self) -> dict:
        # One request covers yesterday, today, and tomorrow. Yesterday keeps
        # delayed final-score corrections; tomorrow handles rescheduled games.
        today = date.today()
        payload = self.api_client.get("/matches", params={
            "dateFrom": (today - timedelta(days=1)).isoformat(),
            "dateTo": (today + timedelta(days=1)).isoformat(),
        })
        if payload is None:
            return {"processed": 0, "updated": 0, "provider_available": False}

        processed = updated = 0
        for provider_match in payload.get("matches", []):
            existing = self.repository.get_match_by_api_id(str(provider_match["id"]))
            if existing is None:
                continue

            processed += 1
            score = provider_match.get("score", {}).get("fullTime", {})
            home_score = score.get("home")
            away_score = score.get("away")
            status = provider_match.get("status", existing.status)
            changed = (
                existing.status != status
                or (home_score is not None and existing.home_score != home_score)
                or (away_score is not None and existing.away_score != away_score)
            )
            if changed:
                existing.status = status
                if home_score is not None:
                    existing.home_score = home_score
                if away_score is not None:
                    existing.away_score = away_score
                self.repository.update_match(existing)
                updated += 1

        return {"processed": processed, "updated": updated, "provider_available": True}


class FutureFixtureSync:
    """Import newly announced fixtures once daily without repeatedly hitting the API."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MatchRepository(db)
        self.api_client = FootballAPIClient()
        self.match_mapper = MatchMapper(db)

    def run(self) -> dict:
        today = date.today()
        payload = self.api_client.get("/matches", params={
            "dateFrom": today.isoformat(),
            "dateTo": (today + timedelta(days=settings.FUTURE_FIXTURE_SYNC_DAYS)).isoformat(),
        })
        if payload is None:
            return {"processed": 0, "created": 0, "skipped": 0, "provider_available": False}

        processed = created = skipped = 0
        for provider_match in payload.get("matches", []):
            processed += 1
            if self.repository.get_match_by_api_id(str(provider_match["id"])):
                continue
            try:
                # A fixture is created only once its competition, season and
                # both teams are mapped locally. This avoids corrupting the DB
                # when a provider announces an unknown club.
                self.repository.create_match(self.match_mapper.create(provider_match))
                created += 1
            except Exception:
                self.db.rollback()
                skipped += 1
        return {"processed": processed, "created": created, "skipped": skipped, "provider_available": True}
