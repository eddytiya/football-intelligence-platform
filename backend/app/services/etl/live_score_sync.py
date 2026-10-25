"""Small, free-tier-friendly score refresh for matches already in our database."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.match_repository import MatchRepository
from app.services.football_api import FootballAPIClient
from app.services.matching.match_mapper import MatchMapper
from app.services.matching.result_validation import validate_provider_match


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

        processed = updated = rejected = 0
        for provider_match in payload.get("matches", []):
            try:
                validate_provider_match(provider_match)
            except (ValueError, KeyError, TypeError):
                rejected += 1
                continue
            existing = self.repository.get_match_by_api_id(str(provider_match["id"]))
            if existing is None:
                continue
            # Reject a reused/mismapped provider ID rather than updating another fixture.
            identity_mismatch = False
            for side in ("home", "away"):
                provider_team_id = (provider_match.get(f"{side}Team") or {}).get("id")
                stored_team = getattr(existing, f"{side}_team", None)
                stored_team_id = getattr(stored_team, "api_id", None)
                if provider_team_id is not None and stored_team_id is not None and provider_team_id != stored_team_id:
                    identity_mismatch = True
                    break
            if identity_mismatch:
                rejected += 1
                continue

            processed += 1
            score = provider_match.get("score", {}).get("fullTime", {})
            home_score = score.get("home")
            away_score = score.get("away")
            status = provider_match.get("status", existing.status)
            kickoff = datetime.fromisoformat(provider_match["utcDate"].replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            changed = (
                existing.status != status
                or existing.utc_date != kickoff
                or (home_score is not None and existing.home_score != home_score)
                or (away_score is not None and existing.away_score != away_score)
            )
            if changed:
                existing.status = status
                existing.utc_date = kickoff
                existing.match_date = kickoff.date()
                existing.kick_off = kickoff.time()
                if home_score is not None:
                    existing.home_score = home_score
                if away_score is not None:
                    existing.away_score = away_score
                try:
                    self.repository.update_match(existing)
                    updated += 1
                except ValueError:
                    self.db.rollback()
                    rejected += 1

        return {"processed": processed, "updated": updated, "rejected": rejected, "provider_available": True}


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
