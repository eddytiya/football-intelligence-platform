from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.etl.live_score_sync import LiveScoreSync


def run_sync(payload, stored):
    updates = []
    sync = LiveScoreSync.__new__(LiveScoreSync)
    sync.db = SimpleNamespace(rollback=lambda: None)
    sync.api_client = SimpleNamespace(get=lambda *a, **k: {"matches": [payload]})
    sync.repository = SimpleNamespace(get_match_by_api_id=lambda key: stored,
                                      update_match=lambda match: updates.append(match))
    return sync.run(), updates


def records():
    kickoff = datetime.now(timezone.utc) - timedelta(days=1)
    payload = {"id": 1, "utcDate": kickoff.isoformat(), "status": "FINISHED",
               "homeTeam": {"id": 10}, "awayTeam": {"id": 20},
               "score": {"fullTime": {"home": 2, "away": 0}}}
    stored = SimpleNamespace(status="SCHEDULED", utc_date=datetime.now() + timedelta(days=1),
                             home_score=0, away_score=0, home_team=SimpleNamespace(api_id=10),
                             away_team=SimpleNamespace(api_id=20))
    return payload, stored, kickoff


def test_sync_corrects_rescheduled_kickoff_before_accepting_final_result():
    payload, stored, kickoff = records()
    result, updates = run_sync(payload, stored)
    assert result["updated"] == 1
    assert stored.utc_date == kickoff.replace(tzinfo=None)
    assert stored.match_date == kickoff.date()
    assert stored.status == "FINISHED"
    assert stored.home_score == 2


def test_sync_rejects_future_finished_provider_payload():
    payload, stored, _ = records()
    payload["utcDate"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    result, updates = run_sync(payload, stored)
    assert result["rejected"] == 1
    assert not updates
    assert stored.status == "SCHEDULED"


def test_provider_id_cannot_update_a_different_clubs_fixture():
    payload, stored, _ = records()
    payload["homeTeam"]["id"] = 99
    result, updates = run_sync(payload, stored)
    assert result["rejected"] == 1
    assert not updates
