"""Create a readable report for the completed local shot-feature experiment."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.paths import REPORTS_DIR


def pct(value):
    return f"{100 * value:.2f}%" if value is not None else "N/A"


def main():
    output = REPORTS_DIR / "shot_feature_experiment"
    report = json.loads((output / "results.json").read_text(encoding="utf-8"))
    folds = json.loads((output / "rolling_folds.json").read_text(encoding="utf-8"))
    chosen = report["chosen_variant"]
    baseline = report["rolling_results"]["baseline"]["overall"]
    candidate = report["rolling_results"][chosen]["overall"]
    gain = candidate["accuracy"] - baseline["accuracy"]
    interval = report["rolling_uncertainty"].get(chosen, {}).get("accuracy_delta_95_interval", [0, 0])
    lines = ["# Past-shot features: free local data experiment", "", "## Outcome", "",
             f"Selected by rolling website log loss: **{chosen}**. The active website artifact was not changed.", "",
             f"The selected forecast scores {pct(candidate['accuracy'])} accuracy and {candidate['log_loss']:.6f} log loss across {candidate['matches']:,} rolling-validation matches. The matched baseline scores {pct(baseline['accuracy'])} and {baseline['log_loss']:.6f}.", "",
             f"Accuracy increases by {gain * 100:.3f} percentage points ({round(gain * candidate['matches'])} additional correct predictions). The paired accuracy interval crosses zero, so the accuracy gain remains uncertain; the log-loss improvement is clearer. Retain the candidate for further testing rather than claiming 60% or changing the active model from these results alone." if chosen != "baseline" and interval[0] <= 0 <= interval[1] else "Review the paired intervals and partial-season results before changing the active model.", "",
             "## Rolling comparisons", "",
             "Three expanding training windows evaluate the full 2023, 2024 and 2025 seasons. Classifiers, preprocessing and goal models fit only earlier dates. The exact website mix is 50% classifier, 25% Elo and 25% goal-model Poisson probabilities.", "",
             "| Features | Matches | Website accuracy | Website log loss | PL accuracy | PL prior-top-six accuracy |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, row in report["rolling_results"].items():
        total, pl, top = row["overall"], row["premier_league"], row["premier_league_prior_top_six"]
        lines.append(f"| {name} | {total['matches']:,} | {pct(total['accuracy'])} | {total['log_loss']:.6f} | {pct(pl['accuracy'])} ({pl['matches']}) | {pct(top['accuracy'])} ({top['matches']}) |")
    lines += ["", "## Individual seasons", "",
              "| Season | Features | Website accuracy | Website log loss | Classifier accuracy | Classifier log loss |",
              "|---|---|---:|---:|---:|---:|"]
    for row in folds:
        website, classifier = row["website_ensemble"]["overall"], row["classifier"]["overall"]
        lines.append(f"| {row['season']} | {row['variant']} | {pct(website['accuracy'])} | {website['log_loss']:.6f} | {pct(classifier['accuracy'])} | {classifier['log_loss']:.6f} |")
    lines += ["", "## Partial 2026 check", "",
              f"Dates: {' to '.join(report['final_dates'])}. Only the baseline and the earlier rolling-selection winner are checked here.", "",
              "| Features | Matches | Website accuracy | Website log loss |",
              "|---|---:|---:|---:|"]
    for name, row in report["final_2026"].items():
        value = row["website_ensemble"]["overall"]
        lines.append(f"| {name} | {value['matches']:,} | {pct(value['accuracy'])} | {value['log_loss']:.6f} |")
    lines += ["", f"Partial-season paired 95% intervals: log-loss difference {report['final_uncertainty']['log_loss_delta_95_interval']}; accuracy difference {report['final_uncertainty']['accuracy_delta_95_interval']}. Both include zero in this run, so the small 2026 sample does not establish a reliable gain by itself."]
    lines += ["", "## Paired uncertainty", "",
              "Calendar weeks are resampled together to retain within-week dependence. These descriptive 95% bootstrap intervals are not adjusted for selection among variants. Differences are candidate minus baseline: negative log-loss differences and positive accuracy differences favour the candidate.", "",
              "| Features | Log-loss difference interval | Accuracy difference interval |",
              "|---|---|---|"]
    for name, row in report["rolling_uncertainty"].items():
        lines.append(f"| {name} | {row['log_loss_delta_95_interval']} | {row['accuracy_delta_95_interval']} |")
    quality = report["data_quality"]
    lines += ["", "## Data and feature definitions", "",
              f"Read {quality['matches']:,} fixtures from existing local CSVs. Complete valid home/away shot pairs: {quality['complete_shot_pairs']:,}; complete shots-on-target pairs: {quality['complete_target_pairs']:,}. Invalid-statistic incidents masked: {quality['invalid_statistic_entries_masked']:,}. No fixture is dropped because its statistics are missing.", "",
              "- **Shots:** last-five/ten fixture averages for shots for/against, shot differences and observed-match counts.",
              "- **Shots on target:** the equivalent last-five/ten target-shot averages, differences and observation counts.",
              "- **Combined:** both groups plus last-ten shot accuracy for/against, defined as total on-target shots divided by total shots on rows with both measurements.", "",
              "Windows count actual fixtures, including those with missing measurements. Missing statistics stay NaN and receive explicit coverage counts; median imputation learns only from the training period. Observed zero shots stay zero. Negative/fractional counts and targets exceeding total shots are treated as invalid, not silently used as valid evidence.", "",
              "Statistics are appended to team history only after that day's feature snapshots have been generated. Current-match shots, current-match goals and future results cannot enter their own pre-match inputs. Rolling histories remain within each competition and may span season changes or long breaks.", "",
              "The classifier receives the additional features. Goal regressors and Elo remain identical between variants within each fold, so this is a controlled classifier-feature test rather than a complete redesign of the website ensemble.", "",
              "## Cost and limits", "",
              "Existing local data only: no subscriptions, purchases, external requests, new accounts or extra datasets are needed for this experiment.", "",
              "The 2026 slice is small and already appeared in earlier production training; it is held out only from this experiment. Earlier historical validation periods have also been inspected. These are not prospective live accuracy measurements, and they must not replace the website's separately recorded 51.84% as though evaluated on the same split.", "",
              "Premier League top-six labels use the previous season's on-pitch table, excluding disciplinary deductions. Shot coverage varies by league and season. No betting odds or current-match expected-goals columns are used.", "",
              "## Validation and reproduction", "",
              "The shot-feature unit tests cover home/away reversal, missing-versus-zero handling, expiry by actual-fixture windows, current-match exclusion and invalid-statistic masking. Rebuilt baseline features and labels exactly match the active artifact. The active artifact SHA-256 is checked before and after the experiment.", "",
              "From the repository root:", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe -m pytest -q",
              ".\\.venv\\Scripts\\python.exe backend/scripts/experiment_shot_features.py",
              ".\\.venv\\Scripts\\python.exe backend/scripts/report_shot_features.py", "```", "",
              "Structured results, individual-season comparisons, per-fixture rolling/final probabilities and a local experimental bundle accompany this report. The bundle and feature cache are excluded from Git and do not replace the website model."]
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output / "README.md")


if __name__ == "__main__":
    main()
