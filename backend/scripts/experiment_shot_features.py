"""Rolling evaluation of lagged shots using existing local free CSVs only."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS
from app.services.machine_learning.shot_features import SHOT_VARIANTS, ShotFeatureModel
from experiment_form_features import attach_top_six, digest, fit_classifier, fit_goal_signals, paired_week_bootstrap, segment_metrics


def main():
    output = REPORTS_DIR / "shot_feature_experiment"
    output.mkdir(exist_ok=True)
    active_hash = digest(MODELS_DIR / "historical_match_model.joblib")
    print("Building lagged shot features from existing local CSVs...", flush=True)
    feature_model = ShotFeatureModel()
    x, y = feature_model.build_training_data()
    examples = pd.DataFrame([{key: value for key, value in row.items() if key != "features"} for row in feature_model.historical_examples])
    examples["match_date"] = pd.to_datetime(examples.match_date)
    examples["prior_top_six"] = attach_top_six(examples)
    dates = examples.match_date
    artifact = joblib.load(MODELS_DIR / "historical_match_model.joblib")
    reference = artifact["historical_examples"]
    assert len(reference) == len(x)
    baseline = pd.DataFrame([{**row["features"], "league": row["league"]} for row in reference], columns=FEATURE_COLUMNS)
    pd.testing.assert_frame_equal(x[FEATURE_COLUMNS], baseline, check_dtype=False)
    assert y.tolist() == [row["result"] for row in reference]
    joblib.dump({"features": x, "target": y, "examples": examples}, output / "features.joblib")
    print(f"Loaded {len(x)} fixtures. Shot quality: {feature_model.stat_quality}", flush=True)
    folds, pooled_frames = [], []
    predictions = {name: [] for name in SHOT_VARIANTS}
    for season in (2023, 2024, 2025):
        start, end = pd.Timestamp(season, 7, 1), pd.Timestamp(season + 1, 7, 1)
        train = np.flatnonzero(dates < start)
        validation = np.flatnonzero((dates >= start) & (dates < end))
        assert dates.iloc[train].max() < dates.iloc[validation].min()
        print(f"Season {season}: training {len(train)}, validation {len(validation)}. Fitting shared goal models...", flush=True)
        signals, _ = fit_goal_signals(x, examples, train, validation)
        frame = examples.iloc[validation].reset_index(drop=True)
        pooled_frames.append(frame)
        for name in SHOT_VARIANTS:
            p, _ = fit_classifier(x, y, train, validation, name, SHOT_VARIANTS)
            ensemble = .5 * p + signals
            predictions[name].append(ensemble)
            result = {"season": season, "variant": name, "training_matches": len(train),
                      "classifier": segment_metrics(y.iloc[validation], p, frame),
                      "website_ensemble": segment_metrics(y.iloc[validation], ensemble, frame)}
            folds.append(result)
            (output / "rolling_folds.json").write_text(json.dumps(folds, indent=2), encoding="utf-8")
            print(f"  {name}: accuracy={result['website_ensemble']['overall']['accuracy']:.3%}, log loss={result['website_ensemble']['overall']['log_loss']:.6f}", flush=True)
    pooled_frame = pd.concat(pooled_frames, ignore_index=True)
    predictions = {key: np.concatenate(value) for key, value in predictions.items()}
    pooled = {name: segment_metrics(pooled_frame.result, p, pooled_frame) for name, p in predictions.items()}
    uncertainty = {name: paired_week_bootstrap(pooled_frame, predictions["baseline"], p)
                   for name, p in predictions.items() if name != "baseline"}
    chosen = min(pooled, key=lambda name: pooled[name]["overall"]["log_loss"])
    print(f"Selected on rolling log loss: {chosen}; checking partial 2026 season...", flush=True)
    train, validation = np.flatnonzero(dates < pd.Timestamp(2026, 7, 1)), np.flatnonzero(dates >= pd.Timestamp(2026, 7, 1))
    signals, goal_bundle = fit_goal_signals(x, examples, train, validation)
    frame = examples.iloc[validation].reset_index(drop=True)
    final, final_probabilities = {}, {}
    for name in dict.fromkeys(["baseline", chosen]):
        p, bundle = fit_classifier(x, y, train, validation, name, SHOT_VARIANTS)
        ensemble = .5 * p + signals
        final_probabilities[name] = ensemble
        final[name] = {"classifier": segment_metrics(y.iloc[validation], p, frame),
                       "website_ensemble": segment_metrics(y.iloc[validation], ensemble, frame)}
        export = frame.copy()
        export[["away_probability", "draw_probability", "home_probability"]] = ensemble
        export.to_csv(output / f"{name}_2026_predictions.csv", index=False)
        if name == chosen:
            joblib.dump({"classifier": bundle, "goal_models": goal_bundle, "variant": chosen,
                         "training_cutoff": "2026-07-01", "note": "Experimental bundle; production model unchanged."}, output / "candidate.joblib")
    # Export rolling forecasts for reproducible paired comparisons, including club identities.
    for name, p in predictions.items():
        export = pooled_frame.copy()
        export[["away_probability", "draw_probability", "home_probability"]] = p
        export.to_csv(output / f"{name}_rolling_predictions.csv", index=False)
    report = {"cost": "Existing local CSVs only; no paid data, subscriptions or external API requests.",
              "data_quality": feature_model.stat_quality,
              "features": {name: len(FEATURE_COLUMNS) + len(extra) for name, extra in SHOT_VARIANTS.items()},
              "rolling_results": pooled, "rolling_uncertainty": uncertainty, "chosen_variant": chosen,
              "final_2026": final,
              "final_uncertainty": paired_week_bootstrap(frame, final_probabilities["baseline"], final_probabilities[chosen]),
              "final_dates": [str(frame.match_date.min().date()), str(frame.match_date.max().date())],
              "limitations": ["2026 is partial and previously inspected; held out only from this experiment.",
                              "Same fixed CatBoost parameters, baseline-feature goal regressors and Elo signals; only outcome classifier receives shot features.",
                              "Missing statistics remain missing, with observed-match counts; imputation fits training data only.",
                              "Calendar-week bootstrap is descriptive and not corrected for selecting among variants.",
                              "Prior-season top six are reconstructed on-pitch standings without point deductions."],
              "active_model_unchanged": active_hash == digest(MODELS_DIR / "historical_match_model.joblib")}
    assert report["active_model_unchanged"]
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
