from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from app.services.machine_learning.historical_match_model import HistoricalMatchModel, TeamState
from app.services.machine_learning.temporal_protocol import PROTOCOL_VERSION
from app.services.matching.result_validation import result_issue, validate_provider_match
from app.services.matching.result_validation import validate_match_record
from types import SimpleNamespace


@pytest.mark.parametrize("provider,archive", [
    ("Leeds United FC", "leeds"), ("Manchester City FC", "mancity"),
    ("Manchester United FC", "manunited"), ("Brighton & Hove Albion FC", "brighton"),
    ("FC Internazionale Milano", "inter"), ("Sport Lisboa e Benfica", "benfica"),
    ("RCD Espanyol de Barcelona", "espanol"),
])
def test_verified_aliases(provider, archive):
    model = HistoricalMatchModel()
    model.known_teams["X"] = {archive, "sheffieldunited", "barcelona", "splisbon"}
    assert model._resolve_team("X", provider) == (archive, 1.)


def test_unknown_club_never_borrows_another_teams_history():
    model = HistoricalMatchModel()
    model.known_teams["PL"] = {"mancity", "sheffieldunited"}
    assert model._resolve_team("PL", "Coventry City FC") == ("coventry", 0.)
    assert model._resolve_team("UNSUPPORTED", "Manchester City FC")[1] == 0


def test_new_season_resets_table_but_retains_elo_and_recent_form():
    model = HistoricalMatchModel()
    model._start_season("PL", 2024, {"A", "B", "Relegated"})
    model._update_states("PL", "A", "B", 2, 0, datetime(2025, 5, 1))
    elo = model.states["PL:a"].elo
    model._start_season("PL", 2025, {"A", "B", "Promoted"})
    assert model.states["PL:a"].games == model.states["PL:a"].points == 0
    assert model.states["PL:a"].elo == elo
    assert list(model.states["PL:a"].recent_results) == [3]
    assert "PL:relegated" not in model.league_members["PL"]
    for team in ("A", "B", "Promoted"):
        assert 1 <= model._league_position("PL", model._state_key("PL", team)) <= 3


def test_features_use_pre_match_state_and_reset_season_counts(monkeypatch):
    model = HistoricalMatchModel()
    matches = pd.DataFrame([
        {"match_date": pd.Timestamp("2024-08-01"), "league": "PL", "season": 2024, "home_team": "A", "away_team": "B", "home_goals": 3, "away_goals": 0},
        {"match_date": pd.Timestamp("2024-08-01"), "league": "PL", "season": 2024, "home_team": "C", "away_team": "D", "home_goals": 1, "away_goals": 0},
        {"match_date": pd.Timestamp("2025-08-01"), "league": "PL", "season": 2025, "home_team": "A", "away_team": "C", "home_goals": 0, "away_goals": 0},
    ])
    monkeypatch.setattr(model, "load_matches", lambda: matches)
    features, target = model.build_training_data()
    assert features.home_games.tolist() == [0, 0, 0]
    assert features.away_games.tolist() == [0, 0, 0]
    assert features.iloc[2].home_elo > 1500
    assert features.iloc[2].home_points_per_game == 0
    assert target.tolist() == [2, 2, 1]
    assert features.iloc[2].home_league_position <= 2


def test_provider_rejects_future_finished_and_invalid_status():
    now = datetime(2026, 10, 17, tzinfo=timezone.utc)
    assert result_issue("FINISHED", now + timedelta(days=1), 1, 0, now)
    assert result_issue("2026-08-08 13:30:00Z", now, 1, 0, now)
    assert result_issue("FINISHED", now - timedelta(days=1), None, 0, now)
    assert result_issue("FINISHED", now - timedelta(days=1), -1, 0, now)
    assert result_issue("FINISHED", now - timedelta(days=1), 0, 0, now) is None
    assert result_issue("SCHEDULED", now + timedelta(days=1), None, None, now) is None


def test_provider_guard_requires_complete_final_score():
    payload = {"utcDate": "2026-10-01T10:00:00Z", "status": "FINISHED", "score": {"fullTime": {"home": None, "away": 0}}}
    with pytest.raises(ValueError, match="scores"):
        validate_provider_match(payload, datetime(2026, 10, 17, tzinfo=timezone.utc))


def test_unknown_fixture_is_rejected_before_estimator_runs():
    model = HistoricalMatchModel()
    model.pipeline = model.home_goals_pipeline = model.away_goals_pipeline = object()
    model.known_teams["PL"] = {"mancity", "leeds"}
    with pytest.raises(ValueError, match="Verified team history"):
        model.predict_fixture("PL", "Coventry City FC", "Leeds United FC", datetime.now() + timedelta(days=1))


def test_historical_fixture_is_not_predicted_with_final_states():
    model = HistoricalMatchModel()
    model.leakage_protocol_version = PROTOCOL_VERSION
    model.training_data_through = "2026-10-10"
    model.pipeline = model.home_goals_pipeline = model.away_goals_pipeline = object()
    model.known_teams["PL"] = {"a", "b"}
    model.states["PL:a"] = TeamState(last_match_date=datetime(2026, 10, 12))
    with pytest.raises(ValueError, match="point-in-time"):
        model.predict_fixture("PL", "A", "B", datetime(2026, 10, 11))


def test_stale_states_cannot_produce_forecasts():
    model = HistoricalMatchModel()
    model.leakage_protocol_version = PROTOCOL_VERSION
    model.training_data_through = (datetime.now() - timedelta(days=2)).date().isoformat()
    model.pipeline = model.home_goals_pipeline = model.away_goals_pipeline = object()
    model.known_teams["PL"] = {"a", "b"}
    model.states["PL:a"] = TeamState(last_match_date=datetime(2000, 1, 1))
    with pytest.raises(ValueError, match="Recent verified results"):
        model.predict_fixture("PL", "A", "B", datetime.now() + timedelta(days=1))


def test_old_club_history_does_not_prove_current_membership():
    model = HistoricalMatchModel()
    model.leakage_protocol_version = PROTOCOL_VERSION
    model.training_data_through = (datetime.now() - timedelta(days=2)).date().isoformat()
    model.pipeline = model.home_goals_pipeline = model.away_goals_pipeline = object()
    model.known_teams["PL"] = {"a", "b"}
    model.states["PL:a"] = TeamState(last_match_date=datetime.now() - timedelta(days=1))
    model.league_members["PL"] = {"PL:a"}
    with pytest.raises(ValueError, match="current-season membership"):
        model.predict_fixture("PL", "A", "B", datetime.now() + timedelta(days=1))


def test_orm_guard_supports_date_only_history_and_rejects_future_results():
    now = datetime(2026, 10, 17, tzinfo=timezone.utc)
    record = SimpleNamespace(status="FINISHED", utc_date=None, match_date=datetime(2026, 10, 12).date(), home_score=1, away_score=0)
    validate_match_record(record, now=now)
    record.match_date = datetime(2026, 10, 18).date()
    with pytest.raises(ValueError, match="future kickoff"):
        validate_match_record(record, now=now)


def test_undated_legacy_update_preserved_but_new_undated_result_rejected():
    record = SimpleNamespace(status="FINISHED", utc_date=None, match_date=None, home_score=1, away_score=0)
    validate_match_record(record, legacy_update=True)
    with pytest.raises(ValueError, match="no kickoff"):
        validate_match_record(record)


def test_website_forecast_uses_exact_ensemble_and_class_order():
    import numpy as np

    class Outcome:
        classes_ = np.array([2, 0, 1])

        def predict_proba(self, x):
            return np.tile([.65, .15, .20], (len(x), 1))

        def predict(self, x):
            return np.full(len(x), 2)

    class Goals:
        def predict(self, x):
            return np.full(len(x), 1.)

    model = HistoricalMatchModel()
    model.leakage_protocol_version = PROTOCOL_VERSION
    model.training_data_through = (datetime.now() - timedelta(days=2)).date().isoformat()
    model.pipeline, model.home_goals_pipeline, model.away_goals_pipeline = Outcome(), Goals(), Goals()
    model.known_teams["PL"] = {"a", "b"}
    model._start_season("PL", 2026, {"A", "B"})
    previous = datetime.now() - timedelta(days=1)
    model.states["PL:a"] = TeamState(last_match_date=previous)
    model.states["PL:b"] = TeamState(last_match_date=previous)
    kickoff = datetime.now() + timedelta(days=1)
    features = model._features("PL", "a", "b", kickoff)
    expected = model._ensemble_probabilities({2: .65, 0: .15, 1: .20}, model._elo_outcome_probabilities(features), model._poisson_outcome_probabilities(1., 1.))
    prediction = model.predict_fixture("PL", "A", "B", kickoff)
    assert prediction["home_win_probability"] == round(expected[2], 4)
    assert prediction["draw_probability"] == round(expected[1], 4)
    assert prediction["away_win_probability"] == round(expected[0], 4)
