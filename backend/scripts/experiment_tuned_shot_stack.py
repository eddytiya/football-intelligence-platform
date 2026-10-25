"""Nested chronological CatBoost tuning and shot-feature goal-model ablation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor
from sklearn.metrics import log_loss, mean_absolute_error
from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel
from app.services.machine_learning.shot_features import SHOT_VARIANTS
from experiment_form_features import digest, paired_week_bootstrap, preprocessor, segment_metrics

SHOT_FEATURES = FEATURE_COLUMNS + SHOT_VARIANTS["shots_combined"]
CLASSIFIER_BASE = dict(iterations=250, depth=6, learning_rate=.05, l2_leaf_reg=5)
CONFIGURATIONS = [CLASSIFIER_BASE, dict(iterations=700, depth=4, learning_rate=.03, l2_leaf_reg=10),
                  dict(iterations=700, depth=6, learning_rate=.03, l2_leaf_reg=10),
                  dict(iterations=700, depth=5, learning_rate=.05, l2_leaf_reg=20)]
VARIANTS = {
    "current_baseline": ("baseline", "baseline"),
    "shots_fixed": ("shots_fixed", "baseline"),
    "shots_tuned": ("shots_tuned", "baseline"),
    "shots_with_shot_goals": ("shots_fixed", "shots"),
    "shots_tuned_with_shot_goals": ("shots_tuned", "shots"),
}
COMMON = dict(verbose=False, random_seed=42, thread_count=4, allow_writing_files=False)


def date_blocks(dates, season):
    start, end = pd.Timestamp(season, 7, 1), pd.Timestamp(season + 1, 7, 1)
    train = np.flatnonzero(dates < start)
    validation = np.flatnonzero((dates >= start) & (dates < end))
    if not len(train) or not len(validation) or dates.iloc[train].max() >= dates.iloc[validation].min():
        raise ValueError("Empty or overlapping chronological blocks")
    return train, validation


def tune_classifier(x, y, dates, outer_season):
    # Last completed season INSIDE the outer training block selects settings/iteration.
    train, validation = date_blocks(dates, outer_season - 1)
    assert dates.iloc[validation].max() < pd.Timestamp(outer_season, 7, 1)
    prep = preprocessor(SHOT_FEATURES)
    train_x, val_x = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[validation])
    trials = []
    for config in CONFIGURATIONS:
        model = CatBoostClassifier(loss_function="MultiClass", **COMMON, **config)
        model.fit(train_x, y.iloc[train], eval_set=(val_x, y.iloc[validation]),
                  early_stopping_rounds=60, use_best_model=True)
        trial = {"parameters": config, "trees": model.tree_count_,
                 "log_loss": float(log_loss(y.iloc[validation], model.predict_proba(val_x), labels=[0, 1, 2]))}
        trials.append(trial)
        print(f"  Inner tuning {outer_season}: depth {config['depth']}, trees {model.tree_count_}, log loss {trial['log_loss']:.6f}", flush=True)
    winner = min(trials, key=lambda row: row["log_loss"])
    return {"inner_validation_season": outer_season - 1, "training_matches": len(train),
            "validation_matches": len(validation), "trials": trials,
            "selected_parameters": {**winner["parameters"], "iterations": winner["trees"]}}


def classifier(x, y, train, validation, columns, parameters):
    prep = preprocessor(columns)
    train_x, val_x = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[validation])
    model = CatBoostClassifier(loss_function="MultiClass", **COMMON, **parameters)
    model.fit(train_x, y.iloc[train])
    assert np.array_equal(model.classes_, [0, 1, 2])
    return model.predict_proba(val_x), {"preprocessor": prep, "model": model, "feature_columns": columns}


def goals(x, examples, train, validation, columns):
    prep = preprocessor(columns)
    train_x, val_x = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[validation])
    models, predicted, errors = {}, {}, {}
    for side in ("home", "away"):
        model = CatBoostRegressor(loss_function="MAE", iterations=300, depth=6,
                                  learning_rate=.05, l2_leaf_reg=5, **COMMON)
        model.fit(train_x, examples.iloc[train][f"{side}_goals"])
        predicted[side] = model.predict(val_x)
        errors[side] = float(mean_absolute_error(examples.iloc[validation][f"{side}_goals"], predicted[side]))
        models[side] = model
    poisson = np.array([[HistoricalMatchModel._poisson_outcome_probabilities(h, a)[c] for c in (0, 1, 2)]
                        for h, a in zip(predicted["home"], predicted["away"])])
    return poisson, errors, {"preprocessor": prep, "models": models, "feature_columns": columns}


def mix(classifier_probabilities, elo, poisson):
    p = .5 * classifier_probabilities + .25 * elo + .25 * poisson
    if not np.isfinite(p).all() or (p < 0).any() or not np.allclose(p.sum(axis=1), 1):
        raise ValueError("Invalid website probability distribution")
    return p


def run_period(x, y, examples, season, variant_names, tuned, tuning_log):
    dates = examples.match_date
    train, validation = date_blocks(dates, season)
    frame = examples.iloc[validation].reset_index(drop=True)
    needed_classifiers = {VARIANTS[name][0] for name in variant_names}
    needed_goals = {VARIANTS[name][1] for name in variant_names}
    params = None
    if "shots_tuned" in needed_classifiers:
        params = tune_classifier(x, y, dates, season)
        tuning_log.append({"outer_season": season, **params})
    print(f"Season {season}: refitting classifiers and goal regressors on {len(train)} earlier matches...", flush=True)
    probabilities, classifier_bundles = {}, {}
    for name in ("baseline", "shots_fixed", "shots_tuned"):
        if name not in needed_classifiers:
            continue
        columns = FEATURE_COLUMNS if name == "baseline" else SHOT_FEATURES
        settings = params["selected_parameters"] if name == "shots_tuned" else CLASSIFIER_BASE
        probabilities[name], classifier_bundles[name] = classifier(x, y, train, validation, columns, settings)
    goal_predictions, goal_errors, goal_bundles = {}, {}, {}
    for name in ("baseline", "shots"):
        if name in needed_goals:
            columns = FEATURE_COLUMNS if name == "baseline" else SHOT_FEATURES
            goal_predictions[name], goal_errors[name], goal_bundles[name] = goals(x, examples, train, validation, columns)
    elo = np.array([[HistoricalMatchModel._elo_outcome_probabilities(row)[c] for c in (0, 1, 2)]
                    for row in x.iloc[validation].to_dict("records")])
    results, forecasts, bundles = [], {}, {}
    for name in variant_names:
        outcome, goal = VARIANTS[name]
        p = mix(probabilities[outcome], elo, goal_predictions[goal])
        forecasts[name] = p
        row = {"season": season, "variant": name, "training_matches": len(train),
               "website_ensemble": segment_metrics(y.iloc[validation], p, frame),
               "classifier": segment_metrics(y.iloc[validation], probabilities[outcome], frame),
               "goal_mae": goal_errors[goal]}
        results.append(row)
        bundles[name] = {"classifier": classifier_bundles[outcome], "goal_models": goal_bundles[goal]}
        print(f"  {name}: accuracy {row['website_ensemble']['overall']['accuracy']:.3%}, log loss {row['website_ensemble']['overall']['log_loss']:.6f}, goal MAE {row['goal_mae']}", flush=True)
    return results, forecasts, frame, bundles


def main():
    output = REPORTS_DIR / "tuned_shot_stack_experiment"
    output.mkdir(exist_ok=True)
    original_hash = digest(MODELS_DIR / "historical_match_model.joblib")
    data = joblib.load(REPORTS_DIR / "shot_feature_experiment" / "features.joblib")
    x, y, examples = data["features"], data["target"], data["examples"]
    reference = joblib.load(MODELS_DIR / "historical_match_model.joblib")["historical_examples"]
    assert len(reference) == len(examples)
    assert examples.result.tolist() == [row["result"] for row in reference]
    assert examples.match_date.tolist() == pd.to_datetime([row["match_date"] for row in reference]).tolist()
    assert (examples.home_team.to_numpy() == [row["home_team"] for row in reference]).all()
    assert (examples.away_team.to_numpy() == [row["away_team"] for row in reference]).all()
    assert (examples.league.to_numpy() == [row["league"] for row in reference]).all()
    print(f"Loaded {len(x)} cached pre-match snapshots. No downloads or paid data.", flush=True)
    folds, tuning, frames = [], [], []
    predictions = {name: [] for name in VARIANTS}
    for season in (2023, 2024, 2025):
        results, forecasts, frame, _ = run_period(x, y, examples, season, list(VARIANTS), True, tuning)
        folds.extend(results)
        frames.append(frame)
        for name, p in forecasts.items():
            predictions[name].append(p)
        (output / "rolling_folds.json").write_text(json.dumps(folds, indent=2), encoding="utf-8")
        (output / "tuning_trials.json").write_text(json.dumps(tuning, indent=2), encoding="utf-8")
    frame = pd.concat(frames, ignore_index=True)
    predictions = {name: np.concatenate(value) for name, value in predictions.items()}
    pooled = {name: segment_metrics(frame.result, p, frame) for name, p in predictions.items()}
    chosen = min(pooled, key=lambda name: pooled[name]["overall"]["log_loss"])
    print(f"Rolling winner: {chosen}. Final 2026 check is separate from selection.", flush=True)
    final_names = list(dict.fromkeys(["current_baseline", "shots_fixed", chosen]))
    final, final_predictions, final_frame, bundles = run_period(x, y, examples, 2026, final_names, True, tuning)
    joblib.dump({**bundles[chosen], "variant": chosen, "training_cutoff": "2026-07-01",
                 "note": "Experimental stack; not the active website artifact."}, output / "candidate.joblib")
    for name, p in predictions.items():
        export = frame.copy()
        export[["away_probability", "draw_probability", "home_probability"]] = p
        export.to_csv(output / f"{name}_rolling_predictions.csv", index=False)
    for name, p in final_predictions.items():
        export = final_frame.copy()
        export[["away_probability", "draw_probability", "home_probability"]] = p
        export.to_csv(output / f"{name}_2026_predictions.csv", index=False)
    report = {"cost": "Existing cached local features only; no purchases or external requests.",
              "protocol": "Inner prior-season tuning inside each outer training window; outer validation seasons 2023/2024/2025; pooled website log loss selects the stack; partial 2026 evaluates frozen selection.",
              "rolling_results": pooled, "rolling_uncertainty": {name: paired_week_bootstrap(frame, predictions["current_baseline"], p)
                  for name, p in predictions.items() if name != "current_baseline"},
              "versus_previous_shot_candidate": {name: paired_week_bootstrap(frame, predictions["shots_fixed"], p)
                  for name, p in predictions.items() if name not in {"current_baseline", "shots_fixed"}},
              "chosen_variant": chosen, "tuning": tuning, "final_2026": final,
              "final_uncertainty": paired_week_bootstrap(final_frame, final_predictions["current_baseline"], final_predictions[chosen]),
              "limitations": ["Historical validation periods and partial 2026 data were inspected in earlier experiments; not fresh prospective evidence.",
                              "CatBoost goal regressors retain their MAE objective and fixed settings; shot inputs are the controlled change.",
                              "Selection prioritises website log loss; report accuracy separately, without forcing draw predictions.",
                              "Bootstrap intervals are descriptive and do not correct for multiple candidate selection.",
                              "Production artifact remains unchanged."],
              "active_model_unchanged": original_hash == digest(MODELS_DIR / "historical_match_model.joblib")}
    assert report["active_model_unchanged"]
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"winner": chosen, "rolling_results": pooled, "final_2026": final}, indent=2), flush=True)


if __name__ == "__main__":
    main()
