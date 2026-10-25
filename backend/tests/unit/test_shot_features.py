from datetime import datetime

import numpy as np
import pandas as pd

from app.services.machine_learning.shot_features import ShotFeatureModel


def test_shots_are_reversed_for_away_team_history():
    model = ShotFeatureModel()
    model._start_season("PL", 2025, {"A", "B"})
    date = datetime(2025, 8, 1)
    model.match_statistics[("PL", pd.Timestamp(date), "A", "B")] = (15., 6., 5., 2.)
    model._update_states("PL", "A", "B", 2, 0, date)
    features = model._features("PL", "B", "A", datetime(2025, 8, 8))
    assert features["home_shots_for_5"] == 6
    assert features["home_shots_against_5"] == 15
    assert features["away_sot_for_5"] == 5
    assert features["home_shot_accuracy_for_10"] == 2 / 6


def test_missing_stats_are_not_observed_zeros_and_windows_are_fixtures():
    model = ShotFeatureModel()
    model._start_season("PL", 2025, {"A", "B"})
    model.match_statistics[("PL", pd.Timestamp("2025-08-01"), "A", "B")] = (10., 4., 0., 0.)
    model._update_states("PL", "A", "B", 0, 0, datetime(2025, 8, 1))
    features = model._features("PL", "A", "B", datetime(2025, 8, 2))
    assert features["home_sot_for_5"] == 0
    assert features["home_sot_observations_5"] == 1
    for day in range(2, 7):
        model._update_states("PL", "A", "B", 0, 0, datetime(2025, 8, day))
    features = model._features("PL", "A", "B", datetime(2025, 8, 7))
    assert np.isnan(features["home_shots_for_5"])
    assert features["home_shot_observations_5"] == 0
    assert features["home_shot_observations_10"] == 1


def test_current_shots_do_not_enter_current_match_features(monkeypatch):
    rows = pd.DataFrame([
        {"league": "PL", "season": 2025, "match_date": pd.Timestamp("2025-08-01"), "home_team": "A", "away_team": "B", "home_goals": 1, "away_goals": 0},
        {"league": "PL", "season": 2025, "match_date": pd.Timestamp("2025-08-08"), "home_team": "B", "away_team": "A", "home_goals": 0, "away_goals": 0},
        {"league": "PL", "season": 2025, "match_date": pd.Timestamp("2025-08-15"), "home_team": "A", "away_team": "B", "home_goals": 1, "away_goals": 0},
    ])
    original, changed = ShotFeatureModel(), ShotFeatureModel()
    for model in (original, changed):
        monkeypatch.setattr(model, "load_matches", lambda: rows)
        model.match_statistics[("PL", pd.Timestamp("2025-08-01"), "A", "B")] = (10., 5., 4., 1.)
        model.match_statistics[("PL", pd.Timestamp("2025-08-08"), "B", "A")] = (8., 10., 2., 4.)
    changed.match_statistics[("PL", pd.Timestamp("2025-08-08"), "B", "A")] = (30., 10., 15., 4.)
    before, _ = original.build_training_data()
    after, _ = changed.build_training_data()
    pd.testing.assert_frame_equal(before.iloc[:2], after.iloc[:2])
    assert before.iloc[2].away_shots_for_5 != after.iloc[2].away_shots_for_5


def test_invalid_stats_masked_without_dropping_matches(tmp_path):
    path = tmp_path / "PL_2025.csv"
    path.write_text("Date,HomeTeam,AwayTeam,FTHG,FTAG,HS,AS,HST,AST\n01/08/2025,A,B,1,0,4,5,9,1\n08/08/2025,B,A,0,0,-1,6,1,2\n", encoding="utf-8")
    model = ShotFeatureModel(tmp_path)
    rows = model.load_matches()
    assert len(rows) == 2
    assert model.stat_quality["invalid_statistic_entries_masked"] == 2
    first = model.match_statistics[("PL", pd.Timestamp("2025-08-01"), "A", "B")]
    assert np.isnan(first[0]) and np.isnan(first[2])
