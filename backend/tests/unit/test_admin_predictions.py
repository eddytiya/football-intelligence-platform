from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pandas as pd
import pytest
from fastapi import HTTPException
from app.api.auth import admin_user
from app.services.machine_learning.historical_match_model import HistoricalMatchModel
from app.services.prediction.admin_review import actual_outcome, genuine_snapshot, replay_model


def test_admin_permission_uses_database_role():
    with pytest.raises(HTTPException) as error:
        admin_user(SimpleNamespace(is_admin=False, email='test@123.com'))
    assert error.value.status_code == 403
    user = SimpleNamespace(is_admin=True)
    assert admin_user(user) is user


def test_only_pre_kickoff_records_count_and_fixture_reschedules_are_checked():
    kickoff = datetime(2026, 10, 18, 12)
    match = SimpleNamespace(utc_date=kickoff)
    snapshot = SimpleNamespace(kind='pre_match', generated_at=kickoff.replace(tzinfo=timezone.utc)-timedelta(hours=1), kickoff_at=kickoff,
        payload={'leakage_protocol_version': 1, 'training_data_through': '2026-10-01', 'history_through': '2026-10-17'})
    assert genuine_snapshot(snapshot, match)
    snapshot.kind = 'retrospective'
    assert not genuine_snapshot(snapshot, match)
    snapshot.kind = 'pre_match'
    match.utc_date = kickoff-timedelta(hours=2)
    assert not genuine_snapshot(snapshot, match)


def test_results_require_finished_status_and_complete_score():
    match = SimpleNamespace(status='IN_PLAY', home_score=2, away_score=1)
    assert actual_outcome(match) is None
    match.status = 'FINISHED'
    assert actual_outcome(match) == 'Home Win'
    match.away_score = 2
    assert actual_outcome(match) == 'Draw'
    match.home_score = None
    assert actual_outcome(match) is None


def test_retrospective_form_excludes_same_day_and_later_results(monkeypatch):
    model = HistoricalMatchModel()
    frame = pd.DataFrame([
        dict(league='PL', season=2026, match_date=datetime(2026,10,1), home_team='Alpha', away_team='Beta', home_goals=1, away_goals=0),
        dict(league='PL', season=2026, match_date=datetime(2026,10,2), home_team='Gamma', away_team='Beta', home_goals=2, away_goals=0),
        dict(league='PL', season=2026, match_date=datetime(2026,10,10), home_team='Alpha', away_team='Beta', home_goals=9, away_goals=0),
        dict(league='PL', season=2026, match_date=datetime(2026,10,11), home_team='Beta', away_team='Alpha', home_goals=8, away_goals=0),
    ])
    monkeypatch.setattr(model, 'load_matches', lambda: frame)
    replay = replay_model(model, 'PL', '2026-10-10', ())
    assert replay.states['PL:alpha'].games == 1
    assert replay.states['PL:alpha'].goals_for == 1
    assert replay.states['PL:beta'].games == 2
    assert len(replay.league_members['PL']) == 3
    assert not model.states
