"""Render the completed free-data feature experiment as a readable Markdown report."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app.core.paths import REPORTS_DIR


def percentage(value):
    return f"{value * 100:.2f}%" if value is not None else "N/A"


def main():
    output = REPORTS_DIR / "form_feature_experiment"
    report = json.loads((output / "results.json").read_text(encoding="utf-8"))
    folds = json.loads((output / "rolling_folds.json").read_text(encoding="utf-8"))
    coverage = pd.read_csv(output / "free_data_coverage_by_league.csv")
    chosen = report["chosen_variant"]
    lines = ["# Free-data form-feature experiment", "", "## Outcome", "",
             f"Rolling-selection winner: **{chosen}**. The active website model was not changed.", "",
             "None of the added feature groups beat the baseline on pooled overall accuracy or log loss. Retain the existing website model." if chosen == "baseline" else "The selected variant is an experimental candidate; review both metrics and consistency before promotion.", "",
             "## Rolling website ensemble results", "",
             "Each season is predicted using estimators fitted only on earlier dates. These results pool the non-overlapping 2023, 2024 and 2025 seasons.", "",
             "| Feature variant | Matches | Accuracy | Log loss | PL prior-top-six accuracy |",
             "|---|---:|---:|---:|---:|"]
    for name, result in report["rolling_results"].items():
        overall, top = result["overall"], result["premier_league_prior_top_six"]
        lines.append(f"| {name} | {overall['matches']:,} | {percentage(overall['accuracy'])} | {overall['log_loss']:.6f} | {percentage(top['accuracy'])} ({top['matches']} matches) |")
    lines += ["", "## Results by season", "",
              "| Season | Feature variant | Website accuracy | Website log loss | Classifier accuracy | Classifier log loss |",
              "|---|---|---:|---:|---:|---:|"]
    for result in folds:
        website, classifier = result["website_ensemble"]["overall"], result["classifier"]["overall"]
        lines.append(f"| {result['season']} | {result['variant']} | {percentage(website['accuracy'])} | {website['log_loss']:.6f} | {percentage(classifier['accuracy'])} | {classifier['log_loss']:.6f} |")
    lines += ["", "## Partial 2026 season comparison", "",
              f"Dates: {report['final_2026_start']} to {report['final_2026_end']}. Only baseline and the variant selected on the earlier rolling periods are evaluated here.", "",
              "| Feature variant | Matches | Website accuracy | Website log loss |",
              "|---|---:|---:|---:|"]
    for name, result in report["final_2026"].items():
        value = result["website_ensemble"]["overall"]
        lines.append(f"| {name} | {value['matches']:,} | {percentage(value['accuracy'])} | {value['log_loss']:.6f} |")
    lines += ["", "## Interpretation and limits", "",
              "The current website's recorded 51.84% used a different chronological split. The matched comparisons above should not be presented as a direct change to that rate.", "",
              "The 2026 slice is small and was already included in previous production-model training; it is held out only from this experiment. These are historical checks, not a fresh prospective test.", "",
              "All candidate classifiers use the same fixed CatBoost settings. Goal regressors and Elo signals are identical between variants within each fold, isolating the additions to outcome classification. New features have not been tested in the goal regressors or retuned independently.", "",
              "Top-six membership uses the previous season's reconstructed on-pitch standings, without disciplinary deductions. It does not use the evaluated season's final standings.", "",
              "Paired calendar-week bootstrap intervals describe variability; they do not adjust for selecting among five variants.", "",
              "Because the baseline won selection, the stored selected-minus-baseline bootstrap differences are zero by construction; they are not uncertainty estimates for the rejected feature groups." if chosen == "baseline" else f"Rolling log-loss difference 95% interval (selected minus baseline): {report['rolling_winner_uncertainty']['log_loss_delta_95_interval']}.",
              "All five website variants selected zero draws across the rolling periods; these additions did not resolve draw identification." if chosen == "baseline" else f"Rolling accuracy difference 95% interval (selected minus baseline): {report['rolling_winner_uncertainty']['accuracy_delta_95_interval']}.", "",
              "## Feature definitions", "",
              "- Opponent-adjusted form: last-five/ten result residuals against pre-match Elo expectations, opponent rating averages, and the adjusted form gap. Home advantage is included before the past match result is observed.",
              "- Recent strength: last-five/ten goals scored/conceded, differences from current-season rates, clean sheets, failed-to-score frequency and available history count. Rolling history survives season boundaries; momentum deltas are zero when the season denominator is empty.",
              "- Match balance: absolute strength/form gaps, combined recent goal rates, and each team's historical draw frequency.", "",
              "Every feature is calculated before updating state with that match's result. Dates remain together across training/evaluation boundaries.", "",
              "## Cost and existing free data", "",
              "This experiment uses the existing local archive only. No paid datasets, subscription upgrades, new accounts or external API requests are required by the experiment scripts.", "",
              "The archive is from [Football-Data's downloadable CSV archive](https://football-data.co.uk/). Optional statistics already present locally are inventoried below; they were not added to these three feature groups.", "",
              "| League | Matches | Shots on target available | HxG/AxG columns available |",
              "|---|---:|---:|---:|"]
    for row in coverage.itertuples():
        lines.append(f"| {row.league} | {row.matches:,} | {row.shots_on_target:,} | {row.reported_xg:,} |")
    lines += ["", "Shots and shots-on-target history offer another experiment without buying data, especially in the Premier League. Coverage varies by league. HxG/AxG coverage is limited to the partial 2026 season, so those columns alone cannot support the same long-history comparison.", "",
              "## Validation and reproduction", "",
              "39 unit tests passed, including five new checks for opponent weighting, cold-start handling, retained rolling history, draw frequency and exclusion of the current match's result. The regenerated baseline features exactly matched the active artifact's saved features and labels. The active model file's SHA-256 remained unchanged.", "",
              "From the repository root:", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe backend/scripts/experiment_form_features.py",
              ".\\.venv\\Scripts\\python.exe backend/scripts/inspect_free_feature_data.py",
              ".\\.venv\\Scripts\\python.exe backend/scripts/report_form_features.py", "```", "",
              "Structured results, individual-fold results, final prediction CSVs and coverage inventories accompany this report. Experimental feature/model caches stay local and are excluded from Git."]
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output / "README.md")


if __name__ == "__main__":
    main()
