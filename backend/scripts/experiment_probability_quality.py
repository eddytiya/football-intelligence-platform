"""Isolated chronological blending and temperature-calibration experiment."""
from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.metrics import log_loss

from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel
from experiment_catboost_recency import scores


def tune_catboost_within_training(x, y, dates, training_indices):
    """Choose settings strictly before the later blend/calibration periods."""
    cutoff = dates.iloc[training_indices[int(len(training_indices) * .75)]]
    inner_train = training_indices[(dates.iloc[training_indices] < cutoff).to_numpy()]
    inner_validation = training_indices[(dates.iloc[training_indices] >= cutoff).to_numpy()]
    configs = [
        {"iterations": 700, "depth": 4, "learning_rate": .03, "l2_leaf_reg": 10},
        {"iterations": 700, "depth": 6, "learning_rate": .03, "l2_leaf_reg": 10},
        {"iterations": 700, "depth": 5, "learning_rate": .05, "l2_leaf_reg": 20},
        {"iterations": 700, "depth": 6, "learning_rate": .05, "l2_leaf_reg": 5},
    ]
    trials = []
    for config in configs:
        pipeline = HistoricalMatchModel._candidate_models()["catboost"]
        pipeline.set_params(**{f"model__{key}": value for key, value in config.items()},
                            model__thread_count=4, model__allow_writing_files=False)
        prep = pipeline.named_steps["features"]
        train_x = prep.fit_transform(x.iloc[inner_train])
        validation_x = prep.transform(x.iloc[inner_validation])
        model = pipeline.named_steps["model"]
        model.fit(train_x, y.iloc[inner_train], eval_set=(validation_x, y.iloc[inner_validation]),
                  early_stopping_rounds=60, use_best_model=True)
        trial = {"parameters": config, "trees": model.tree_count_,
                 **scores(y.iloc[inner_validation], model.predict_proba(validation_x))}
        trials.append(trial)
        print(f"Inner tuning {len(trials)}/4: depth={config['depth']}, trees={model.tree_count_}, log loss={trial['log_loss']:.6f}", flush=True)
    best = min(trials, key=lambda row: row["log_loss"])
    return {"cutoff": str(cutoff.date()), "train_matches": len(inner_train),
            "validation_matches": len(inner_validation), "trials": trials,
            "chosen_parameters": {**best["parameters"], "iterations": best["trees"]}}


def temperature_scale(probabilities, temperature):
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    return softmax(np.log(np.clip(probabilities, 1e-15, 1)) / temperature, axis=1)


def fit_temperature(probabilities, target):
    result = minimize_scalar(
        lambda log_t: log_loss(target, temperature_scale(probabilities, np.exp(log_t)), labels=[0, 1, 2]),
        bounds=(np.log(.25), np.log(4)), method="bounded",
    )
    if not result.success:
        raise RuntimeError("Temperature optimisation failed")
    return float(np.exp(result.x))


def best_weights(probabilities, target):
    candidates = []
    for first in range(11):
        for second in range(11 - first):
            weights = np.array([first, second, 10 - first - second]) / 10
            blended = np.einsum("m,mnc->nc", weights, probabilities)
            candidates.append((log_loss(target, blended, labels=[0, 1, 2]), weights))
    return min(candidates, key=lambda item: item[0])[1]


def apply_recipe(probabilities, recipe):
    adjusted = np.stack([temperature_scale(p, t) for p, t in zip(probabilities, recipe["temperatures"])])
    blended = np.einsum("m,mnc->nc", recipe["weights"], adjusted)
    return temperature_scale(blended, recipe["blend_temperature"])


def validate_probabilities(p):
    if not np.isfinite(p).all() or (p < 0).any() or not np.allclose(p.sum(axis=1), 1):
        raise ValueError("Invalid probability distribution")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tuned-catboost", action="store_true",
                        help="Tune CatBoost within the training block before blending and calibration")
    args = parser.parse_args()
    output = REPORTS_DIR / ("tuned_blend_experiment" if args.tuned_catboost else "probability_quality_experiment")
    output.mkdir(exist_ok=True)
    artifact = joblib.load(MODELS_DIR / "historical_match_model.joblib")
    examples = artifact["historical_examples"]
    x = pd.DataFrame([{**e["features"], "league": e["league"]} for e in examples], columns=FEATURE_COLUMNS)
    y = pd.Series([e["result"] for e in examples])
    dates = pd.Series(pd.to_datetime([e["match_date"] for e in examples]))
    order = np.argsort(dates.to_numpy(), kind="stable")
    x, y, dates = (v.iloc[order].reset_index(drop=True) for v in (x, y, dates))
    starts = [dates.iloc[int(len(x) * fraction)] for fraction in (.6, .7, .8)]
    calibration_start, selection_start, test_start = starts
    blocks = {
        "train": np.flatnonzero(dates < calibration_start),
        "calibration": np.flatnonzero((dates >= calibration_start) & (dates < selection_start)),
        "selection": np.flatnonzero((dates >= selection_start) & (dates < test_start)),
        "test": np.flatnonzero(dates >= test_start),
    }
    if x.isna().all().any() or any(not len(indices) for indices in blocks.values()):
        raise ValueError("Missing features or empty chronological block")
    for left, right in zip(list(blocks.values()), list(blocks.values())[1:]):
        assert dates.iloc[left].max() < dates.iloc[right].min()
    models = HistoricalMatchModel._candidate_models()
    names = list(models)
    models["catboost"].set_params(model__thread_count=4, model__allow_writing_files=False)
    models["lightgbm"].set_params(model__n_jobs=4)
    tuning_details = None
    if args.tuned_catboost:
        tuning_details = tune_catboost_within_training(x, y, dates, blocks["train"])
        models["catboost"].set_params(**{f"model__{key}": value
                                       for key, value in tuning_details["chosen_parameters"].items()})
    probabilities = {key: [] for key in ("calibration", "selection", "test")}
    print(f"Blocks: { {key: len(value) for key, value in blocks.items()} }", flush=True)
    for name, model in models.items():
        print(f"Training {name}...", flush=True)
        model.fit(x.iloc[blocks["train"]], y.iloc[blocks["train"]])
        assert np.array_equal(model.classes_, [0, 1, 2])
        for key in probabilities:
            p = model.predict_proba(x.iloc[blocks[key]])
            validate_probabilities(p)
            probabilities[key].append(p)
    probabilities = {key: np.stack(value) for key, value in probabilities.items()}
    cal_y = y.iloc[blocks["calibration"]]
    temperatures = [fit_temperature(p, cal_y) for p in probabilities["calibration"]]
    recipes = {}
    for index, name in enumerate(names):
        weights = np.eye(3)[index].tolist()
        recipes[name] = {"weights": weights, "temperatures": [1.] * 3, "blend_temperature": 1.}
        recipes[f"{name}_calibrated"] = {"weights": weights, "temperatures": temperatures, "blend_temperature": 1.}
    raw_weights = best_weights(probabilities["calibration"], cal_y)
    recipes["blend"] = {"weights": raw_weights.tolist(), "temperatures": [1.] * 3, "blend_temperature": 1.}
    raw_blend = apply_recipe(probabilities["calibration"], recipes["blend"])
    recipes["blend_calibrated"] = {**recipes["blend"], "blend_temperature": fit_temperature(raw_blend, cal_y)}
    calibrated = np.stack([temperature_scale(p, t) for p, t in zip(probabilities["calibration"], temperatures)])
    recipes["calibrated_models_blend"] = {"weights": best_weights(calibrated, cal_y).tolist(),
                                          "temperatures": temperatures, "blend_temperature": 1.}
    selection = []
    for name, recipe in recipes.items():
        p = apply_recipe(probabilities["selection"], recipe)
        validate_probabilities(p)
        selection.append({"name": name, **scores(y.iloc[blocks["selection"]], p), "recipe": recipe})
    selection.sort(key=lambda row: row["log_loss"])
    winner = selection[0]["name"]
    print(f"Selection winner: {winner}", flush=True)
    results = {}
    for name in dict.fromkeys(["catboost", winner]):
        p = apply_recipe(probabilities["test"], recipes[name])
        validate_probabilities(p)
        results[name] = scores(y.iloc[blocks["test"]], p)
        pd.DataFrame({"date": dates.iloc[blocks["test"]].to_numpy(), "actual": y.iloc[blocks["test"]].to_numpy(),
                      "away_probability": p[:, 0], "draw_probability": p[:, 1], "home_probability": p[:, 2]}).to_csv(
                          output / f"{name}_test_predictions.csv", index=False)
    report = {"catboost_variant": "tuned" if args.tuned_catboost else "fixed",
              "catboost_tuning": tuning_details,
              "model_order": names, "blocks": {key: {"matches": len(indices),
              "start": str(dates.iloc[indices].min().date()), "end": str(dates.iloc[indices].max().date())}
              for key, indices in blocks.items()}, "selection_results": selection, "winner": winner,
              "test_results": results,
              "limitations": ["Models remain frozen after the first 60%; no refit after calibration.",
                              "Compare with this experiment's same-training-data CatBoost baseline.",
                              "Final test overlaps previously inspected validation data; not a fresh holdout.",
                              "Only temperature scaling tested; calibration improvement is not guaranteed.",
                              "Production model unchanged."]}
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    joblib.dump({"models": models, "model_order": names, "recipe": recipes[winner],
                 "feature_columns": FEATURE_COLUMNS, "note": "Experimental bundle; not a production artifact."}, output / "candidate.joblib")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
