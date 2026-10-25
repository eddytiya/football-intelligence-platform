"""Render saved experiment results without refitting models."""
import json
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parents[1] / 'reports' / 'shot_context_experiment'
    report = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    lines = ['# Shot context experiment', '', report['cost'], '',
             'Full validation seasons 2023–2025 use expanding chronological training. The website blend remains 50% classifier, 25% Elo and 25% goal-based Poisson. Only lagged shot context and the goal objective change.', '',
             '| Variant | Matches | Accuracy | Log loss |', '| --- | ---: | ---: | ---: |']
    for name, metrics in report['rolling_results'].items():
        score = metrics['overall']
        lines.append(f"| {name} | {score['matches']} | {score['accuracy']:.2%} | {score['log_loss']:.5f} |")
    lines += ['', f"Selected by pooled rolling log loss: **{report['chosen_variant']}**.", '',
              'Partial 2026 check (previously inspected data, not a fresh prospective holdout):', '',
              '| Variant | Matches | Accuracy | Log loss |', '| --- | ---: | ---: | ---: |']
    for row in report['final_2026']:
        score = row['website_ensemble']['overall']
        lines.append(f"| {row['variant']} | {score['matches']} | {score['accuracy']:.2%} | {score['log_loss']:.5f} |")
    lines += ['', 'Neither target (55% overall accuracy and log loss below 0.95) was achieved. The serving artifact remains unchanged; the control reproduced earlier probability forecasts within 1e-12.', '',
              'The selected combined variant reduces pooled log loss by about 0.00042 but loses 18 correct outcomes. Opponent adjustment alone adds just two correct outcomes. These results do not justify claiming a meaningful accuracy improvement.', '',
              'Uncertainty intervals (candidate minus control; calendar-week bootstrap, descriptive only):', '',
              '```json', json.dumps(report['uncertainty'], indent=2), '```', '',
              'Opponent adjustment normalizes shots by the opponent’s previous ten-match attacking/defensive rate, shrunk toward prior league averages with five pseudo-observations. League averages are frozen within each match day. Venue features summarize the last five/ten fixtures at the relevant venue. Missing statistics stay missing. Poisson heads predict positive expected goals using exponentiated raw scores.', '',
              *report['limitations'], '', 'Validation: 50 unit tests passed; a real CatBoost Poisson smoke check confirmed exponentiated expected-goal predictions. No paid data, purchases or downloads.']
    (folder / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('chosen_variant', 'active_model_unchanged', 'uncertainty')}, indent=2))


if __name__ == '__main__':
    main()
