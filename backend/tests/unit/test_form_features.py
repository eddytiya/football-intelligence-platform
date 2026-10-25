from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.services.machine_learning.form_features import EXPERIMENT_COLUMNS, FormFeatureModel
from app.services.machine_learning.historical_match_model import TeamState


def test_beating_a_strong_opponent_receives_larger_adjusted_result():
    model = FormFeatureModel()
    model._start_season("PL", 2025, {"A", "B", "Strong", "Weak"})
    model.states["PL:strong"] = TeamState(elo=1800)
    model.states["PL:weak"] = TeamState(elo=1200)
    model._update_states("PL", "A", "Strong", 1, 0, datetime(2025, 8, 1))
    model._update_states("PL", "B", "Weak", 1, 0, datetime(2025, 8, 1))
    features = model._features("PL", "A", "B", datetime(2025, 8, 8))
    assert features["home_opponent_adjusted_result_5"] > features["away_opponent_adjusted_result_5"]
    assert features["home_opponent_elo_5"] == 1800
    assert features["away_opponent_elo_5"] == 1200


def test_recent_strength_and_new_season_cold_start():
    model = FormFeatureModel()
    model._start_season("PL", 2024, {"A", "B", "C"})
    model._update_states("PL", "A", "B", 2, 0, datetime(2025, 5, 1))
    model._update_states("PL", "A", "C", 0, 1, datetime(2025, 5, 8))
    features = model._features("PL", "A", "B", datetime(2025, 5, 15))
    assert features["home_recent_scored_5"] == 1.
    assert features["home_recent_conceded_5"] == .5
    assert features["home_recent_clean_sheet_rate_5"] == .5
    assert features["home_recent_failed_to_score_rate_5"] == .5
    model._start_season("PL", 2025, {"A", "B", "C"})
    features = model._features("PL", "A", "B", datetime(2025, 8, 1))
    assert features["home_games"] == 0
    assert features["home_recent_matches_available"] == 2
    assert features["home_attack_change_5"] == features["home_defence_change_5"] == 0.


def test_experimental_features_are_finite_for_new_clubs():
    model = FormFeatureModel()
    model._start_season("PL", 2025, {"A", "B"})
    features = model._features("PL", "A", "B", datetime(2025, 8, 1))
    assert set(EXPERIMENT_COLUMNS) == set(features)
    assert np.isfinite([value for key, value in features.items() if key != "league"]).all()
    assert features["home_recent_draw_rate_10"] == 0


def test_current_match_result_cannot_change_its_own_features(monkeypatch):
    records = [
        {"match_date": pd.Timestamp("2025-08-01"), "league": "PL", "season": 2025, "home_team": "A", "away_team": "B", "home_goals": 1, "away_goals": 0},
        {"match_date": pd.Timestamp("2025-08-08"), "league": "PL", "season": 2025, "home_team": "B", "away_team": "A", "home_goals": 0, "away_goals": 0},
        {"match_date": pd.Timestamp("2025-08-15"), "league": "PL", "season": 2025, "home_team": "A", "away_team": "B", "home_goals": 0, "away_goals": 1},
    ]
    original, changed = FormFeatureModel(), FormFeatureModel()
    monkeypatch.setattr(original, "load_matches", lambda: pd.DataFrame(records))
    altered = [dict(row) for row in records]
    altered[-1]["home_goals"] = 9
    monkeypatch.setattr(changed, "load_matches", lambda: pd.DataFrame(altered))
    x_before, y_before = original.build_training_data()
    x_after, y_after = changed.build_training_data()
    pd.testing.assert_frame_equal(x_before, x_after)
    assert y_before.iloc[-1] != y_after.iloc[-1]


def test_match_balance_captures_recent_draw_frequency():
    model = FormFeatureModel()
    model._start_season("PL", 2025, {"A", "B"})
    model._update_states("PL", "A", "B", 0, 0, datetime(2025, 8, 1))
    features = model._features("PL", "B", "A", datetime(2025, 8, 8))
    assert features["home_recent_draw_rate_10"] == features["away_recent_draw_rate_10"] == 1.
    assert features["absolute_season_ppg_gap"] == 0.
    assert features["combined_recent_goal_rate_5"] == 0.
