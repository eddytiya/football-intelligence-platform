"""Validate provider results before they can become historical training truth."""
from datetime import datetime, timezone

VALID_STATUSES = {"SCHEDULED", "TIMED", "IN_PLAY", "PAUSED", "FINISHED", "SUSPENDED", "POSTPONED", "CANCELLED", "AWARDED"}


def result_issue(status, kickoff, home_score, away_score, now=None):
    now = now or datetime.now(timezone.utc)
    if status not in VALID_STATUSES:
        return "Unrecognised match status"
    if status != "FINISHED":
        return None
    if kickoff is None:
        return "Finished match has no kickoff date"
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if kickoff > now:
        return "Finished match has a future kickoff"
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (home_score, away_score)):
        return "Finished match has missing or invalid full-time scores"
    return None


def validate_provider_match(payload, now=None):
    kickoff = datetime.fromisoformat(payload["utcDate"].replace("Z", "+00:00"))
    score = (payload.get("score") or {}).get("fullTime") or {}
    issue = result_issue(payload.get("status"), kickoff, score.get("home"), score.get("away"), now)
    if issue:
        raise ValueError(issue)


def validate_match_record(record, *, legacy_update=False, now=None):
    """Shared ORM write guard, including importers that do not use MatchMapper."""
    if record.status == "QUARANTINED":
        return
    kickoff = record.utc_date
    if kickoff is None and record.match_date is not None:
        kickoff = datetime.combine(record.match_date, datetime.min.time())
    if legacy_update and record.status == "FINISHED" and kickoff is None:
        return
    issue = result_issue(record.status, kickoff, record.home_score, record.away_score, now)
    if issue:
        raise ValueError(issue)
