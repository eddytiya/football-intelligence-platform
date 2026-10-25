import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import experiment_tuned_shot_stack as experiment


def test_chronological_blocks_keep_boundary_dates_out_of_training():
    dates = pd.Series(pd.to_datetime(["2022-06-30", "2023-06-30", "2023-07-01", "2023-07-01", "2024-07-01"]))
    train, validation = experiment.date_blocks(dates, 2023)
    assert train.tolist() == [0, 1]
    assert validation.tolist() == [2, 3]


def test_empty_chronological_period_is_rejected():
    with pytest.raises(ValueError):
        experiment.date_blocks(pd.Series(pd.to_datetime(["2023-07-01"])), 2023)


def test_tuning_cannot_observe_outer_validation_season(monkeypatch):
    dates = pd.Series(pd.to_datetime(["2021-06-30", "2022-06-30", "2022-07-01", "2023-06-30", "2023-07-01", "2024-01-01"]))
    x = pd.DataFrame({"marker": np.arange(6)})
    y = pd.Series([0, 1, 0, 1, 2, 2])
    observed = []

    class Prep:
        def fit_transform(self, frame):
            return frame.to_numpy()

        def transform(self, frame):
            return frame.to_numpy()

    class Model:
        tree_count_ = 7

        def __init__(self, **kwargs):
            pass

        def fit(self, train_x, target, eval_set, **kwargs):
            observed.append((train_x.flatten().tolist(), eval_set[0].flatten().tolist()))

        def predict_proba(self, frame):
            return np.tile([.4, .4, .2], (len(frame), 1))

    monkeypatch.setattr(experiment, "preprocessor", lambda columns: Prep())
    monkeypatch.setattr(experiment, "CatBoostClassifier", Model)
    monkeypatch.setattr(experiment, "CONFIGURATIONS", [experiment.CLASSIFIER_BASE])
    result = experiment.tune_classifier(x, y, dates, 2023)
    assert observed == [([0, 1], [2, 3])]
    assert result["selected_parameters"]["iterations"] == 7


def test_website_mix_preserves_probability_distribution():
    classifier = np.array([[.2, .3, .5]])
    elo, poisson = np.array([[.1, .2, .7]]), np.array([[.3, .4, .3]])
    actual = experiment.mix(classifier, elo, poisson)
    np.testing.assert_allclose(actual, [[.2, .3, .5]])
    with pytest.raises(ValueError):
        experiment.mix(np.ones((1, 3)), elo, poisson)
