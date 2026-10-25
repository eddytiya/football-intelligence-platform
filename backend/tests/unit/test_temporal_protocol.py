from datetime import datetime, timedelta
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from app.services.machine_learning.temporal_protocol import calibration_folds, chronological_splits, verified_cutoffs
from app.services.machine_learning.historical_match_model import HistoricalMatchModel, FEATURE_COLUMNS, NUMERIC_FEATURES
from app.services.machine_learning.temporal_training import fit_walk_forward
from app.services.prediction.admin_review import genuine_snapshot


def test_date_blocks_are_disjoint_and_never_split_the_same_day():
    dates = pd.date_range('2024-01-01', periods=40).repeat(3)
    train, selection, test = chronological_splits(dates)
    assert dates[train].max() < dates[selection].min() < dates[test].min()
    assert dates[selection].max() < dates[test].min()
    assert set(train) | set(selection) | set(test) == set(range(len(dates)))
    for earlier, later in calibration_folds(dates):
        assert dates[earlier].max() < dates[later].min()


def test_calibration_preprocessing_is_fitted_inside_each_earlier_fold():
    dates = pd.date_range('2024-01-01', periods=40).repeat(3)
    features = pd.DataFrame({key: (['PL'] * len(dates) if key == 'league' else np.arange(len(dates), dtype=float)) for key in FEATURE_COLUMNS})
    model = HistoricalMatchModel._candidate_models(dates)['calibrated_logistic_regression']
    model.fit(features, np.tile([0,1,2], 40))
    first = model.named_steps['model'].calibrated_classifiers_[0].estimator
    imputer = first.named_steps['features'].named_transformers_['numeric'].named_steps['imputer']
    earlier, _ = calibration_folds(dates)[0]
    np.testing.assert_allclose(imputer.statistics_, features.iloc[earlier][NUMERIC_FEATURES].median())


def test_old_or_same_day_training_metadata_never_counts_as_verified():
    payload = {'leakage_protocol_version': 1, 'training_data_through':'2026-10-01','history_through':'2026-10-17'}
    assert verified_cutoffs(payload, datetime(2026,10,18))
    assert not verified_cutoffs({}, datetime(2026,10,18))
    assert not verified_cutoffs({**payload, 'training_data_through':'2026-10-18'}, datetime(2026,10,18))
    assert not verified_cutoffs({**payload, 'history_through':'2026-10-19'}, datetime(2026,10,18))
    old = SimpleNamespace(kind='pre_match', generated_at=datetime(2026,10,17),kickoff_at=datetime(2026,10,18),payload={})
    assert not genuine_snapshot(old,SimpleNamespace(utc_date=datetime(2026,10,18)))


def test_changing_future_results_cannot_change_earlier_model(monkeypatch):
    dates = pd.date_range('2024-01-01', periods=600)
    frame = pd.DataFrame([dict(match_date=day, league='PL',season=day.year if day.month>=7 else day.year-1,
        home_team='Alpha',away_team='Beta',home_goals=i%3,away_goals=1) for i,day in enumerate(dates)])
    monkeypatch.setattr(HistoricalMatchModel,'load_matches',lambda self:frame.copy())
    earlier = fit_walk_forward(HistoricalMatchModel(), '2025-06-01')
    weights = earlier.pipeline.named_steps['model'].coef_.copy()
    version = earlier.model_version
    frame.loc[frame.match_date >= '2025-06-01','home_goals'] = 50
    frame.loc[frame.match_date >= '2025-06-01','home_team'] = 'Future Club'
    repeated = fit_walk_forward(HistoricalMatchModel(), '2025-06-01')
    assert repeated.model_version == version
    np.testing.assert_array_equal(repeated.pipeline.named_steps['model'].coef_,weights)
    assert repeated.training_data_through == '2025-05-31'
    assert 'futureclub' not in repeated.known_teams['PL']
