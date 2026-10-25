from datetime import datetime
import numpy as np
import pandas as pd
from app.services.machine_learning.shot_context_features import ShotContextModel


def test_venue_history_keeps_home_and_away_separate():
    model = ShotContextModel()
    model._start_season('PL', 2025, {'A', 'B'})
    day = datetime(2025, 8, 1)
    model.match_statistics[('PL', pd.Timestamp(day), 'A', 'B')] = (15., 6., 5., 2.)
    model._update_states('PL', 'A', 'B', 2, 0, day)
    features = model._features('PL', 'B', 'A', datetime(2025, 8, 8))
    assert features['home_venue_shot_observations_5'] == 0
    assert np.isnan(features['home_venue_shots_for_5'])
    same = model._features('PL', 'A', 'B', datetime(2025, 8, 8))
    assert same['home_venue_shots_for_5'] == 15
    assert same['away_venue_shots_for_5'] == 6


def test_opponent_defence_adjusts_attacking_shots():
    model = ShotContextModel()
    strong, weak = ('PL', 'strong'), ('PL', 'weak')
    model.shot_history[strong].append((13., 5., 4., 1.))
    model.shot_history[weak].append((13., 25., 4., 8.))
    observed = (12., 10., 4., 3.)
    assert model.adjusted_record('PL', strong, observed)[0] > model.adjusted_record('PL', weak, observed)[0]
    assert model.adjusted_record('PL', ('PL', 'new'), observed) == observed


def test_current_match_statistics_do_not_change_its_features(monkeypatch):
    rows = pd.DataFrame([dict(league='PL', season=2025, match_date=pd.Timestamp(f'2025-08-{day:02}'), home_team='A', away_team='B', home_goals=1, away_goals=0) for day in (1, 8, 15)])
    models = [ShotContextModel(), ShotContextModel()]
    for model, shots in zip(models, (10., 30.)):
        monkeypatch.setattr(model, 'load_matches', lambda: rows)
        model.match_statistics[('PL', pd.Timestamp('2025-08-08'), 'A', 'B')] = (shots, 5., 4., 1.)
    before, _ = models[0].build_training_data()
    after, _ = models[1].build_training_data()
    pd.testing.assert_frame_equal(before.iloc[:2], after.iloc[:2])
    assert before.iloc[2].home_adjusted_shots_for_5 != after.iloc[2].home_adjusted_shots_for_5
