"""Compare three free-data feature groups with rolling chronological evaluation."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.form_features import EXPERIMENT_COLUMNS, FEATURE_GROUPS, FormFeatureModel
from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel

VARIANTS = {"baseline": [], **{key: columns for key, columns in FEATURE_GROUPS.items()},
            "all_three": [column for columns in FEATURE_GROUPS.values() for column in columns]}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preprocessor(columns):
    return ColumnTransformer([("league", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["league"]),
                              ("numbers", SimpleImputer(strategy="median"), [c for c in columns if c != "league"])])


def measure(y, p):
    if not len(y):
        return {"matches": 0, "accuracy": None, "log_loss": None}
    assert np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(axis=1), 1)
    predicted = p.argmax(axis=1)
    draws = np.asarray(y) == 1
    return {"matches": len(y), "accuracy": float(accuracy_score(y, predicted)),
            "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
            "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
            "predicted_draws": int((predicted == 1).sum()),
            "correct_draws": int(((predicted == 1) & draws).sum()),
            "draw_recall": float((predicted[draws] == 1).mean()) if draws.any() else None}


def segment_metrics(y, p, frame):
    pl = (frame.league == "PL").to_numpy()
    top = pl & frame.prior_top_six.to_numpy()
    return {"overall": measure(y, p), "premier_league": measure(np.asarray(y)[pl], p[pl]),
            "premier_league_prior_top_six": measure(np.asarray(y)[top], p[top])}


def attach_top_six(matches):
    prior = {}
    for (league, season), part in matches.groupby(["league", "season"]):
        table = {}
        for row in part.itertuples():
            for team, gf, ga in ((row.home_team, row.home_goals, row.away_goals), (row.away_team, row.away_goals, row.home_goals)):
                stats = table.setdefault(team, [0, 0, 0])
                stats[0] += 3 if gf > ga else 1 if gf == ga else 0
                stats[1] += gf - ga
                stats[2] += gf
        prior[(league, int(season) + 1)] = set(sorted(table, key=lambda t: tuple(-v for v in table[t]) + (t,))[:6])
    return [row.home_team in prior.get((row.league, row.season), set())
            or row.away_team in prior.get((row.league, row.season), set()) for row in matches.itertuples()]


def fit_goal_signals(x, examples, train, validation):
    prep = preprocessor(FEATURE_COLUMNS)
    train_x, val_x = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[validation])
    models, predicted = {}, {}
    for side in ("home", "away"):
        model = CatBoostRegressor(loss_function="MAE", iterations=300, depth=6, learning_rate=.05,
                                  l2_leaf_reg=5, verbose=False, random_seed=42, thread_count=4, allow_writing_files=False)
        model.fit(train_x, examples.iloc[train][f"{side}_goals"])
        models[side] = model
        predicted[side] = model.predict(val_x)
    elo = np.array([[HistoricalMatchModel._elo_outcome_probabilities(row)[c] for c in (0, 1, 2)]
                    for row in x.iloc[validation].to_dict("records")])
    poisson = np.array([[HistoricalMatchModel._poisson_outcome_probabilities(h, a)[c] for c in (0, 1, 2)]
                        for h, a in zip(predicted["home"], predicted["away"])])
    return .25 * elo + .25 * poisson, {"preprocessor": prep, "models": models}


def fit_classifier(x, y, train, validation, variant, variants=None):
    columns = FEATURE_COLUMNS + (variants if variants is not None else VARIANTS)[variant]
    prep = preprocessor(columns)
    train_x, val_x = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[validation])
    model = CatBoostClassifier(loss_function="MultiClass", iterations=250, depth=6, learning_rate=.05,
                              l2_leaf_reg=5, verbose=False, random_seed=42, thread_count=4, allow_writing_files=False)
    model.fit(train_x, y.iloc[train])
    assert np.array_equal(model.classes_, [0, 1, 2])
    return model.predict_proba(val_x), {"preprocessor": prep, "model": model, "feature_columns": columns}


def paired_week_bootstrap(frame, baseline, candidate, draws=1000):
    """Descriptive uncertainty with calendar weeks, preserving within-week dependence."""
    target = frame.result.to_numpy(dtype=int)
    indices = np.arange(len(target))
    base_loss = -np.log(np.clip(baseline[indices, target], 1e-15, 1))
    new_loss = -np.log(np.clip(candidate[indices, target], 1e-15, 1))
    differences = pd.DataFrame({"week": frame.match_date.dt.to_period("W").astype(str),
                                "loss": new_loss - base_loss,
                                "accuracy": (candidate.argmax(axis=1) == target).astype(float) - (baseline.argmax(axis=1) == target).astype(float),
                                "count": 1}).groupby("week")[["loss", "accuracy", "count"]].sum().to_numpy()
    rng = np.random.default_rng(42)
    sampled = differences[rng.integers(0, len(differences), size=(draws, len(differences)))].sum(axis=1)
    return {"log_loss_delta_95_interval": np.quantile(sampled[:, 0] / sampled[:, 2], [.025, .975]).tolist(),
            "accuracy_delta_95_interval": np.quantile(sampled[:, 1] / sampled[:, 2], [.025, .975]).tolist(),
            "note": "Paired calendar-week bootstrap; descriptive, not adjusted for selecting among variants."}


def main():
    output = REPORTS_DIR / "form_feature_experiment"
    output.mkdir(exist_ok=True)
    active_hash = digest(MODELS_DIR / "historical_match_model.joblib")
    feature_model = FormFeatureModel()
    print("Rebuilding pre-match features from existing free local history...", flush=True)
    x, y = feature_model.build_training_data()
    examples = pd.DataFrame([{key: value for key, value in row.items() if key != "features"}
                             for row in feature_model.historical_examples])
    examples["match_date"] = pd.to_datetime(examples.match_date)
    examples["prior_top_six"] = attach_top_six(examples)
    dates = examples.match_date
    reference = joblib.load(MODELS_DIR / "historical_match_model.joblib")["historical_examples"]
    if len(reference) == len(x):
        reference_x = pd.DataFrame([{**row["features"], "league": row["league"]} for row in reference], columns=FEATURE_COLUMNS)
        pd.testing.assert_frame_equal(x[FEATURE_COLUMNS], reference_x, check_dtype=False)
        assert y.tolist() == [row["result"] for row in reference]
    joblib.dump({"features": x, "target": y, "examples": examples}, output / "features.joblib")
    print(f"Loaded {len(x)} matches; {len(FEATURE_COLUMNS)} baseline and {len(EXPERIMENT_COLUMNS) - len(FEATURE_COLUMNS)} experimental features.", flush=True)
    folds, pooled_predictions, pooled_frames = [], {name: [] for name in VARIANTS}, []
    for season in (2023, 2024, 2025):
        start, end = pd.Timestamp(season, 7, 1), pd.Timestamp(season + 1, 7, 1)
        train, validation = np.flatnonzero(dates < start), np.flatnonzero((dates >= start) & (dates < end))
        assert len(train) and len(validation) and dates.iloc[train].max() < dates.iloc[validation].min()
        print(f"Season {season}: train {len(train)}; evaluate {len(validation)}. Fitting fixed goal signals...", flush=True)
        fixed_signals, _ = fit_goal_signals(x, examples, train, validation)
        frame = examples.iloc[validation].reset_index(drop=True)
        pooled_frames.append(frame)
        for name in VARIANTS:
            p, _ = fit_classifier(x, y, train, validation, name)
            ensemble = .5 * p + fixed_signals
            pooled_predictions[name].append(ensemble)
            result = {"season": season, "variant": name, "training_matches": len(train),
                      "classifier": segment_metrics(y.iloc[validation], p, frame),
                      "website_ensemble": segment_metrics(y.iloc[validation], ensemble, frame)}
            folds.append(result)
            (output / "rolling_folds.json").write_text(json.dumps(folds, indent=2), encoding="utf-8")
            print(f"  {name}: website accuracy={result['website_ensemble']['overall']['accuracy']:.3%}; log loss={result['website_ensemble']['overall']['log_loss']:.6f}", flush=True)
    pooled_frame = pd.concat(pooled_frames, ignore_index=True)
    pooled_predictions = {key: np.concatenate(value) for key, value in pooled_predictions.items()}
    pooled = {name: segment_metrics(pooled_frame.result, p, pooled_frame) for name, p in pooled_predictions.items()}
    chosen = min(pooled, key=lambda name: pooled[name]["overall"]["log_loss"])
    print(f"Rolling-selection winner: {chosen}. Evaluating baseline and winner on 2026 season only...", flush=True)
    train = np.flatnonzero(dates < pd.Timestamp(2026, 7, 1))
    validation = np.flatnonzero(dates >= pd.Timestamp(2026, 7, 1))
    fixed_signals, goal_bundle = fit_goal_signals(x, examples, train, validation)
    final, final_predictions = {}, {}
    frame = examples.iloc[validation].reset_index(drop=True)
    for name in dict.fromkeys(["baseline", chosen]):
        p, bundle = fit_classifier(x, y, train, validation, name)
        ensemble = .5 * p + fixed_signals
        final_predictions[name] = ensemble
        final[name] = {"classifier": segment_metrics(y.iloc[validation], p, frame),
                       "website_ensemble": segment_metrics(y.iloc[validation], ensemble, frame)}
        export = frame.copy()
        export[["away_probability", "draw_probability", "home_probability"]] = ensemble
        export.to_csv(output / f"{name}_2026_predictions.csv", index=False)
        if name == chosen:
            joblib.dump({"classifier": bundle, "goal_models": goal_bundle, "variant": chosen,
                         "training_cutoff": "2026-07-01", "note": "Experimental bundle, not the active website model."}, output / "candidate.joblib")
    report = {"cost": "No paid data, API subscriptions or additional downloads; existing local provider archive only.",
              "matches": len(x), "feature_counts": {name: len(FEATURE_COLUMNS) + len(columns) for name, columns in VARIANTS.items()},
              "protocol": "Expanding training windows; validate 2023, 2024, 2025 seasons; select by pooled website log loss; evaluate selected variant and baseline on partial 2026 season.",
              "fixed_components": "Same baseline-feature goal regressors and Elo signals for every variant within a fold; additions affect outcome classifier only.",
              "rolling_results": pooled, "chosen_variant": chosen,
              "rolling_winner_uncertainty": paired_week_bootstrap(pooled_frame, pooled_predictions["baseline"], pooled_predictions[chosen]),
              "final_2026": final, "final_2026_start": str(frame.match_date.min().date()), "final_2026_end": str(frame.match_date.max().date()),
              "final_winner_uncertainty": paired_week_bootstrap(frame, final_predictions["baseline"], final_predictions[chosen]),
              "limitations": ["2026 data is partial and already included in the deployed model's earlier training; it is held out only for this experiment.",
                              "Historical evaluation data has been inspected in previous experiments; not a pristine holdout.",
                              "Prior-season top-six labels reconstruct on-pitch standings without disciplinary deductions.",
                              "Goal regressors do not yet use the new features; production model unchanged."],
              "active_model_unchanged": active_hash == digest(MODELS_DIR / "historical_match_model.joblib")}
    assert report["active_model_unchanged"]
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
