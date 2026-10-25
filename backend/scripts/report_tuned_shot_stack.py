"""Summarise completed classifier tuning and shot-feature goal-model tests."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from app.core.paths import REPORTS_DIR


def pct(value):
    return f"{100 * value:.2f}%" if value is not None else "N/A"


def verify_controls(output):
    columns = ["away_probability", "draw_probability", "home_probability"]
    keys = ["league", "match_date", "home_team", "away_team", "result"]
    old = REPORTS_DIR / "shot_feature_experiment"
    for current, previous in (("current_baseline", "baseline"), ("shots_fixed", "shots_combined")):
        left = pd.read_csv(output / f"{current}_rolling_predictions.csv")
        right = pd.read_csv(old / f"{previous}_rolling_predictions.csv")
        pd.testing.assert_frame_equal(left[keys], right[keys])
        np.testing.assert_allclose(left[columns], right[columns], rtol=0, atol=1e-12)
    return True


def main():
    output = REPORTS_DIR / "tuned_shot_stack_experiment"
    report = json.loads((output / "results.json").read_text(encoding="utf-8"))
    (output / "tuning_trials.json").write_text(json.dumps(report["tuning"], indent=2), encoding="utf-8")
    folds = json.loads((output / "rolling_folds.json").read_text(encoding="utf-8"))
    assert verify_controls(output)
    chosen = report["chosen_variant"]
    selected = report["rolling_results"][chosen]["overall"]
    previous = report["rolling_results"]["shots_fixed"]["overall"]
    lines = ["# Tuned shot classifier and shot-feature goal regressors", "", "## Outcome", "",
             f"Selected by pooled rolling website log loss: **{chosen}**. The active website artifact was not changed.", "",
             f"Compared with the previous shot candidate, rolling accuracy is {pct(selected['accuracy'])} versus {pct(previous['accuracy'])}; log loss is {selected['log_loss']:.6f} versus {previous['log_loss']:.6f}. The best rolling result uses fixed classifier settings and shot features in both goal regressors. Tuning did not beat that stack in this grid.", "",
             "The partial 2026 check is mixed: shot-based goal models improve overall accuracy over the previous shot candidate but worsen log loss. Premier League top-six rolling accuracy also declines slightly. This does not establish a general accuracy upgrade or justify claiming 60%; retain the candidate for further validation and keep the active website model unchanged.", "",
             "Controls reproduce the preceding shot experiment's exact rolling match identities, outcome labels and probabilities to absolute tolerance 1e-12.", "",
             "## Rolling comparisons", "",
             "Evaluate the full 2023, 2024 and 2025 seasons using expanding training windows. Settings and tree counts are selected on the prior completed season inside each training window. No outer validation-season labels fit or tune its estimators.", "",
             "| Forecast | Matches | Accuracy | Log loss | Home goal MAE | Away goal MAE | PL prior-top-six accuracy |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, row in report["rolling_results"].items():
        total, top = row["overall"], row["premier_league_prior_top_six"]
        parts = [part for part in folds if part["variant"] == name]
        denominator = sum(part["website_ensemble"]["overall"]["matches"] for part in parts)
        goal_errors = {side: sum(part["goal_mae"][side] * part["website_ensemble"]["overall"]["matches"] for part in parts) / denominator for side in ("home", "away")}
        lines.append(f"| {name} | {total['matches']:,} | {pct(total['accuracy'])} | {total['log_loss']:.6f} | {goal_errors['home']:.4f} | {goal_errors['away']:.4f} | {pct(top['accuracy'])} ({top['matches']}) |")
    lines += ["", "Variant definitions:", "",
              "- `current_baseline`: current fixed-settings classifier and goal regressors, all using baseline features.",
              "- `shots_fixed`: previous 52.19% rolling candidate; fixed shot classifier with baseline goal models.",
              "- `shots_tuned`: nested-tuned shot classifier with baseline goal models.",
              "- `shots_with_shot_goals`: fixed shot classifier and shot features in both goal regressors.",
              "- `shots_tuned_with_shot_goals`: tuned shot classifier and shot features in both goal regressors.", "",
              "Goal MAE measures goal prediction error, not match-outcome accuracy. All variants use the exact website probability combination: 50% classifier, 25% Elo, 25% Poisson from the two goal regressors.", "",
              "## By season", "",
              "| Season | Forecast | Accuracy | Log loss | Home goal MAE | Away goal MAE |",
              "|---|---|---:|---:|---:|---:|"]
    for row in folds:
        total = row["website_ensemble"]["overall"]
        lines.append(f"| {row['season']} | {row['variant']} | {pct(total['accuracy'])} | {total['log_loss']:.6f} | {row['goal_mae']['home']:.4f} | {row['goal_mae']['away']:.4f} |")
    lines += ["", "## Selected tuning settings", "",
              "Classifier log loss selects settings within the earlier inner season; pooled outer website log loss selects the final stack. The tuning grid includes depths 4/5/6, learning rates 0.03/0.05 and L2 values 5/10/20 in four predefined combinations. Early stopping chooses tree count, with patience 60 and a maximum of 250 or 700 trees depending on configuration.", "",
              "| Outer test season | Inner tuning season | Trees | Depth | Learning rate | L2 |",
              "|---|---|---:|---:|---:|---:|"]
    for row in report["tuning"]:
        settings = row["selected_parameters"]
        lines.append(f"| {row['outer_season']} | {row['inner_validation_season']} | {settings['iterations']} | {settings['depth']} | {settings['learning_rate']} | {settings['l2_leaf_reg']} |")
    lines += ["", "## Partial 2026 check", "",
              "Only the current baseline, previous fixed shot candidate and the stack selected on earlier periods are checked. The 559-row partial season was inspected previously and is not a fresh prospective holdout.", "",
              "| Forecast | Matches | Accuracy | Log loss | Home goal MAE | Away goal MAE |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in report["final_2026"]:
        total = row["website_ensemble"]["overall"]
        lines.append(f"| {row['variant']} | {total['matches']:,} | {pct(total['accuracy'])} | {total['log_loss']:.6f} | {row['goal_mae']['home']:.4f} | {row['goal_mae']['away']:.4f} |")
    lines += ["", "## Paired uncertainty", "",
              "Calendar-week bootstrap intervals are descriptive and not corrected for choosing among candidates. Differences are candidate minus reference: lower log loss and higher accuracy are favourable. Accuracy differences below are proportions, not percentage points.", "",
              "| Forecast | Reference | Log-loss difference 95% interval | Accuracy difference 95% interval |",
              "|---|---|---|---|"]
    for reference, field in (("current_baseline", "rolling_uncertainty"), ("shots_fixed", "versus_previous_shot_candidate")):
        for name, row in report[field].items():
            lines.append(f"| {name} | {reference} | {row['log_loss_delta_95_interval']} | {row['accuracy_delta_95_interval']} |")
    lines += ["", "## Cost, safety checks and limits", "",
              "No paid services, downloads or additional datasets were used. Reused the local 47,738-row pre-match feature cache from the preceding experiment. Current-shot features remain excluded from the current prediction; missing statistics are handled by training-only imputation and explicit coverage counts.", "",
              "47 unit tests passed, including chronological boundary checks, a mocked tuning test that proves the outer season is excluded, and website probability validation. The original model file's SHA-256 remained unchanged. The two control forecasts reproduced the previous experiment exactly.", "",
              "Goal regressors retain their fixed MAE objective and existing hyperparameters; their controlled change is the addition of lagged shot features. A lower goal MAE does not necessarily imply lower outcome log loss.", "",
              "Historical periods and the partial 2026 slice were used in earlier experiments. These results do not establish 60% live accuracy. Prior-season top-six labels reconstruct on-pitch results without disciplinary deductions. The current website's earlier 51.84% metric uses a different split; compare the matched controls in this report.", "",
              "## Reproduce", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe -m pytest -q",
              ".\\.venv\\Scripts\\python.exe backend/scripts/experiment_tuned_shot_stack.py",
              ".\\.venv\\Scripts\\python.exe backend/scripts/report_tuned_shot_stack.py", "```", "",
              "Prerequisite: `shot_feature_experiment/features.joblib` from the earlier shot-feature run. This report directory contains complete tuning trials, period metrics, per-match predictions and an experimental candidate bundle. The bundle is not a drop-in production artifact and remains excluded from Git."]
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "verification.json").write_text(json.dumps({"controls_reproduce_previous_experiment": True,
        "active_model_unchanged": report["active_model_unchanged"], "rolling_comparisons": len(folds),
        "tuning_periods": len(report["tuning"]), "selected_variant": chosen}, indent=2), encoding="utf-8")
    print(output / "README.md")


if __name__ == "__main__":
    main()
