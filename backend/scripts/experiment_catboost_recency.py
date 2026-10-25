"""Run an isolated CatBoost tuning/recency experiment; never replace live artifacts.

Run from backend: ..\\.venv\\Scripts\\python.exe scripts/experiment_catboost_recency.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss

from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel


def scores(y, probabilities):
    return {
        "log_loss": float(log_loss(y, probabilities, labels=[0, 1, 2])),
        "accuracy": float(accuracy_score(y, probabilities.argmax(axis=1))),
        "balanced_accuracy": float(balanced_accuracy_score(y, probabilities.argmax(axis=1))),
    }


def training_rows(dates, end, strategy):
    eligible = dates < end
    if strategy == "recent_3_years":
        eligible &= dates >= end - pd.DateOffset(years=3)
    indices = np.flatnonzero(eligible)
    weights = np.ones(len(indices))
    if strategy == "half_life_2_years":
        age_days = (end - dates.iloc[indices]).dt.total_seconds().to_numpy() / 86400
        weights = np.exp2(-age_days / (365.25 * 2))
        weights /= weights.mean()
    return indices, weights


def main():
    output = REPORTS_DIR / "catboost_recency_experiment"
    output.mkdir(exist_ok=True)
    artifact = joblib.load(MODELS_DIR / "historical_match_model.joblib")
    examples = artifact["historical_examples"]
    x = pd.DataFrame([{**e["features"], "league": e["league"]} for e in examples], columns=FEATURE_COLUMNS)
    y = pd.Series([e["result"] for e in examples])
    dates = pd.Series(pd.to_datetime([e["match_date"] for e in examples]))
    order = np.argsort(dates.to_numpy(), kind="stable")
    x, y, dates = (v.iloc[order].reset_index(drop=True) for v in (x, y, dates))
    tune_start, test_start = dates.iloc[int(len(x) * .6)], dates.iloc[int(len(x) * .8)]
    tuning = np.flatnonzero((dates >= tune_start) & (dates < test_start))
    test = np.flatnonzero(dates >= test_start)
    if x.isna().all().any() or not len(tuning) or not len(test):
        raise ValueError("Missing feature columns or empty evaluation period")
    if not dates.iloc[tuning].max() < dates.iloc[test].min():
        raise ValueError("Tuning and final evaluation periods must not overlap")
    configs = [
        {"iterations": 250, "depth": 6, "learning_rate": .05, "l2_leaf_reg": 5},
        {"iterations": 700, "depth": 4, "learning_rate": .03, "l2_leaf_reg": 10},
        {"iterations": 700, "depth": 6, "learning_rate": .03, "l2_leaf_reg": 10},
        {"iterations": 700, "depth": 5, "learning_rate": .05, "l2_leaf_reg": 20},
    ]
    common = dict(loss_function="MultiClass", random_seed=42, thread_count=4,
                  verbose=False, allow_writing_files=False)
    trials = []
    print(f"Loaded {len(x)} snapshots. Tune from {tune_start.date()}; test from {test_start.date()}.", flush=True)
    for strategy in ("all_history", "recent_3_years", "half_life_2_years"):
        indices, weights = training_rows(dates, tune_start, strategy)
        prep = HistoricalMatchModel._preprocessor(dense=True)
        train_x = prep.fit_transform(x.iloc[indices])
        tune_x = prep.transform(x.iloc[tuning])
        for config in configs:
            candidate = CatBoostClassifier(**common, **config)
            candidate.fit(train_x, y.iloc[indices], sample_weight=weights,
                          eval_set=(tune_x, y.iloc[tuning]), early_stopping_rounds=60,
                          use_best_model=True)
            trial = {"strategy": strategy, "parameters": config, "trees": candidate.tree_count_,
                     "training_matches": len(indices), **scores(y.iloc[tuning], candidate.predict_proba(tune_x))}
            trials.append(trial)
            (output / "tuning_trials.json").write_text(json.dumps(trials, indent=2), encoding="utf-8")
            print(f"Trial {len(trials)}/12: {strategy}, depth={config['depth']}, trees={candidate.tree_count_}, log loss={trial['log_loss']:.5f}, accuracy={trial['accuracy']:.2%}", flush=True)
    winner = min(trials, key=lambda t: t["log_loss"])
    # Only the tuning winner and the fixed baseline see the final evaluation.
    evaluations = {}
    for name, strategy, config in (
        ("baseline", "all_history", configs[0]),
        ("tuning_winner", winner["strategy"], {**winner["parameters"], "iterations": winner["trees"]}),
    ):
        indices, weights = training_rows(dates, test_start, strategy)
        prep = HistoricalMatchModel._preprocessor(dense=True)
        train_x = prep.fit_transform(x.iloc[indices])
        candidate = CatBoostClassifier(**common, **config)
        candidate.fit(train_x, y.iloc[indices], sample_weight=weights)
        probabilities = candidate.predict_proba(prep.transform(x.iloc[test]))
        evaluations[name] = {"strategy": strategy, "parameters": config,
                             "training_matches": len(indices), **scores(y.iloc[test], probabilities)}
        pd.DataFrame({"date": dates.iloc[test].to_numpy(), "actual": y.iloc[test].to_numpy(),
                      "away_probability": probabilities[:, 0], "draw_probability": probabilities[:, 1],
                      "home_probability": probabilities[:, 2]}).to_csv(output / f"{name}_test_predictions.csv", index=False)
        if name == "tuning_winner":
            joblib.dump({"preprocessor": prep, "model": candidate, "feature_columns": FEATURE_COLUMNS,
                         "note": "Experimental outcome model only; not a production HistoricalMatchModel artifact."},
                        output / "candidate.joblib")
    report = {"tune_start": str(tune_start.date()), "test_start": str(test_start.date()),
              "test_end": str(dates.max().date()), "tuning_matches": len(tuning), "test_matches": len(test),
              "previous_saved_metrics": artifact["metrics"], "winner_on_tuning": winner,
              "test_results": evaluations,
              "limitations": ["Final test overlaps the previously reported validation period; it is not new unseen data.",
                              "Single chronological tuning period; confirm with rolling evaluation before deployment.",
                              "Same-day fixtures remain together. Features use prior results as matches unfold.",
                              "Production model was not modified."]}
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
