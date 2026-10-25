"""Evaluate draw weighting on repaired features without forcing draw forecasts."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor
from sklearn.metrics import confusion_matrix
from app.core.paths import REPORTS_DIR
from app.services.machine_learning.historical_match_model import HistoricalMatchModel, FEATURE_COLUMNS
from experiment_catboost_recency import scores


def metrics(y, p):
    predicted = p.argmax(axis=1)
    actual_draws = y.to_numpy() == 1
    return {**scores(y, p), "predicted_draws": int((predicted == 1).sum()),
            "correct_draws": int(((predicted == 1) & actual_draws).sum()),
            "draw_recall": float((predicted[actual_draws] == 1).mean()),
            "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1, 2]).tolist()}


def main():
    output = REPORTS_DIR / "data_repairs"
    artifact = joblib.load(output / "repaired_model.joblib")
    examples = artifact["historical_examples"]
    x = pd.DataFrame([{**r["features"], "league": r["league"]} for r in examples], columns=FEATURE_COLUMNS)
    y = pd.Series([r["result"] for r in examples])
    dates = pd.Series(pd.to_datetime([r["match_date"] for r in examples]))
    train_end, test_start = dates.iloc[int(len(x) * .6)], dates.iloc[int(len(x) * .8)]
    train, selection, test = (np.flatnonzero(mask) for mask in (dates < train_end, (dates >= train_end) & (dates < test_start), dates >= test_start))
    prep = HistoricalMatchModel._preprocessor(dense=True)
    train_x = prep.fit_transform(x.iloc[train])
    transformed = {"selection": prep.transform(x.iloc[selection]), "test": prep.transform(x.iloc[test])}
    goals = {}
    for side in ("home", "away"):
        model = CatBoostRegressor(loss_function="MAE", iterations=300, depth=6, learning_rate=.05,
                                  l2_leaf_reg=5, verbose=False, random_seed=42, thread_count=4, allow_writing_files=False)
        model.fit(train_x, [examples[index][f"{side}_goals"] for index in train])
        goals[side] = {key: model.predict(values) for key, values in transformed.items()}
    signals = {}
    for key, indices in (("selection", selection), ("test", test)):
        elo = np.array([[HistoricalMatchModel._elo_outcome_probabilities(row)[c] for c in (0, 1, 2)] for row in x.iloc[indices].to_dict("records")])
        poisson = np.array([[HistoricalMatchModel._poisson_outcome_probabilities(h, a)[c] for c in (0, 1, 2)] for h, a in zip(goals["home"][key], goals["away"][key])])
        signals[key] = .25 * elo + .25 * poisson
    trials, models = [], {}
    for weight in (1., 1.25, 1.5, 2.):
        model = CatBoostClassifier(loss_function="MultiClass", iterations=250, depth=6, learning_rate=.05,
                                  l2_leaf_reg=5, class_weights=[1, weight, 1], verbose=False,
                                  random_seed=42, thread_count=4, allow_writing_files=False)
        model.fit(train_x, y.iloc[train])
        models[weight] = model
        p = .5 * model.predict_proba(transformed["selection"]) + signals["selection"]
        trial = {"draw_weight": weight, **metrics(y.iloc[selection], p)}
        trials.append(trial)
        print(json.dumps(trial), flush=True)
    winner = min(trials, key=lambda trial: trial["log_loss"])["draw_weight"]
    evaluation = {}
    for weight in dict.fromkeys([1., winner]):
        p = .5 * models[weight].predict_proba(transformed["test"]) + signals["test"]
        evaluation[str(weight)] = metrics(y.iloc[test], p)
    report = {"selection": trials, "chosen_draw_weight": winner, "final_evaluation": evaluation,
              "training_matches": len(train), "selection_matches": len(selection), "test_matches": len(test),
              "note": "Weights chosen on earlier selection period; final rows reused from prior experiments. Production decision unchanged."}
    (output / "draw_weighting.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
