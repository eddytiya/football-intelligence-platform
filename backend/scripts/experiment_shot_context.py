"""Controlled chronological experiment; never replaces the serving artifact."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error
from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.historical_match_model import HistoricalMatchModel
from app.services.machine_learning.shot_context_features import ShotContextModel, ADJUSTED_COLUMNS, VENUE_COLUMNS
from experiment_tuned_shot_stack import SHOT_FEATURES, CLASSIFIER_BASE, COMMON, classifier, date_blocks, mix
from experiment_form_features import digest, preprocessor, segment_metrics, paired_week_bootstrap

COLS = {'shots': SHOT_FEATURES, 'adjusted': SHOT_FEATURES + ADJUSTED_COLUMNS,
        'venue': SHOT_FEATURES + VENUE_COLUMNS, 'all': SHOT_FEATURES + ADJUSTED_COLUMNS + VENUE_COLUMNS}
VARIANTS = {'control': ('shots', 'MAE'), 'opponent_adjusted': ('adjusted', 'MAE'),
            'venue_form': ('venue', 'MAE'), 'poisson_goals': ('shots', 'Poisson'), 'combined': ('all', 'Poisson')}

def goal_prediction(model, values, objective):
    return model.predict(values, prediction_type='Exponent') if objective == 'Poisson' else model.predict(values)

def run_period(x, y, examples, season, names):
    train, valid = date_blocks(examples.match_date, season)
    frame = examples.iloc[valid].reset_index(drop=True)
    elo = np.array([[HistoricalMatchModel._elo_outcome_probabilities(row)[c] for c in (0, 1, 2)] for row in x.iloc[valid].to_dict('records')])
    classes, class_bundles = {}, {}
    for key in dict.fromkeys(VARIANTS[n][0] for n in names):
        classes[key], class_bundles[key] = classifier(x, y, train, valid, COLS[key], CLASSIFIER_BASE)
    records, forecasts, bundles = [], {}, {}
    for name in names:
        key, objective = VARIANTS[name]
        prep = preprocessor(COLS[key])
        tx, vx = prep.fit_transform(x.iloc[train]), prep.transform(x.iloc[valid])
        models, rates, errors = {}, {}, {}
        for side in ('home', 'away'):
            model = CatBoostRegressor(loss_function=objective, iterations=300, depth=6, learning_rate=.05, l2_leaf_reg=5, **COMMON)
            model.fit(tx, examples.iloc[train][f'{side}_goals'])
            rates[side] = goal_prediction(model, vx, objective)
            errors[side] = float(mean_absolute_error(frame[f'{side}_goals'], rates[side]))
            models[side] = model
        poisson = np.array([[HistoricalMatchModel._poisson_outcome_probabilities(h, a)[c] for c in (0, 1, 2)] for h, a in zip(rates['home'], rates['away'])])
        p = mix(classes[key], elo, poisson)
        forecasts[name] = p
        record = dict(season=season, variant=name, training_matches=len(train), website_ensemble=segment_metrics(frame.result, p, frame), goal_mae=errors)
        records.append(record)
        bundles[name] = dict(classifier=class_bundles[key], goal_models=dict(preprocessor=prep, models=models, feature_columns=COLS[key], objective=objective, prediction_type='Exponent' if objective == 'Poisson' else 'RawFormulaVal'))
        score = record['website_ensemble']['overall']
        print(f"{season} {name}: accuracy {score['accuracy']:.4%}, log loss {score['log_loss']:.6f}", flush=True)
    return records, forecasts, frame, bundles

def main():
    output = REPORTS_DIR / 'shot_context_experiment'
    output.mkdir(exist_ok=True)
    active = MODELS_DIR / 'historical_match_model.joblib'
    original = digest(active)
    previous = joblib.load(REPORTS_DIR / 'shot_feature_experiment' / 'features.joblib')
    print('Building strictly lagged context from existing free local data...', flush=True)
    model = ShotContextModel()
    cache = output / 'features.joblib'
    if '--reuse-features' in sys.argv and cache.exists():
        cached = joblib.load(cache)
        x, y = cached['features'], cached['target']
    else:
        x, y = model.build_training_data()
    pd.testing.assert_frame_equal(x[SHOT_FEATURES], previous['features'][SHOT_FEATURES])
    assert y.tolist() == previous['target'].tolist()
    examples = previous['examples']
    if model.historical_examples:
        assert [(r['league'], r['home_team'], r['away_team'], pd.Timestamp(r['match_date'])) for r in model.historical_examples] == list(examples[['league', 'home_team', 'away_team', 'match_date']].itertuples(index=False, name=None))
    joblib.dump(dict(features=x, target=y, examples=examples), output / 'features.joblib')
    folds, frames = [], []
    predictions = {n: [] for n in VARIANTS}
    for season in (2023, 2024, 2025):
        rows, probs, frame, _ = run_period(x, y, examples, season, list(VARIANTS))
        folds.extend(rows); frames.append(frame)
        for n, p in probs.items(): predictions[n].append(p)
        (output / 'rolling_folds.json').write_text(json.dumps(folds, indent=2), encoding='utf-8')
    frame = pd.concat(frames, ignore_index=True)
    predictions = {n: np.concatenate(p) for n, p in predictions.items()}
    reference = pd.read_csv(REPORTS_DIR / 'tuned_shot_stack_experiment' / 'shots_with_shot_goals_rolling_predictions.csv')
    assert np.allclose(predictions['control'], reference[['away_probability', 'draw_probability', 'home_probability']], atol=1e-12, rtol=0)
    pooled = {n: segment_metrics(frame.result, p, frame) for n, p in predictions.items()}
    winner = min(pooled, key=lambda n: pooled[n]['overall']['log_loss'])
    print(f'Frozen rolling selection: {winner}; checking partial 2026.', flush=True)
    final, final_predictions, final_frame, bundles = run_period(x, y, examples, 2026, list(dict.fromkeys(['control', winner])))
    joblib.dump(dict(**bundles[winner], variant=winner, training_cutoff='2026-07-01', note='Experimental only; not a serving artifact'), output / 'candidate.joblib')
    for suffix, export_frame, values in [('rolling', frame, predictions), ('2026', final_frame, final_predictions)]:
        for n, p in values.items():
            export = export_frame.copy()
            export[['away_probability', 'draw_probability', 'home_probability']] = p
            export.to_csv(output / f'{n}_{suffix}_predictions.csv', index=False)
    report = dict(cost='Existing free local CSVs; no downloads or paid services.', chosen_variant=winner,
                  rolling_results=pooled, final_2026=final, rolling_folds=folds,
                  uncertainty={n: paired_week_bootstrap(frame, predictions['control'], p) for n, p in predictions.items() if n != 'control'},
                  active_model_unchanged=original == digest(active), control_reproduced=True,
                  limitations=['Previously inspected historical periods, not fresh prospective validation.', 'Selection by pooled log loss; accuracy is reported separately.', 'Partial 2026 is small and was previously inspected.', 'Bootstrap intervals are descriptive, without multiple-selection correction.'])
    assert report['active_model_unchanged']
    (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    lines = ['# Shot context experiment', '', report['cost'], '', 'Expanding chronological validation: full seasons 2023–2025; same website blend (50% classifier, 25% Elo, 25% goal-based Poisson). Fixed CatBoost settings; only inputs and goal objective change.', '', '| Variant | Matches | Accuracy | Log loss |', '| --- | ---: | ---: | ---: |']
    for n, metrics in pooled.items():
        s = metrics['overall']; lines.append(f"| {n} | {s['matches']} | {s['accuracy']:.2%} | {s['log_loss']:.5f} |")
    lines += ['', f'Selected by rolling log loss: **{winner}**.', '', 'Partial 2026 check:', '', '| Variant | Matches | Accuracy | Log loss |', '| --- | ---: | ---: | ---: |']
    for row in final:
        s = row['website_ensemble']['overall']; lines.append(f"| {row['variant']} | {s['matches']} | {s['accuracy']:.2%} | {s['log_loss']:.5f} |")
    lines += ['', 'The serving model is unchanged. The 55% accuracy / below 0.95 log-loss targets must be judged against these measured results.', '', *report['limitations']]
    (output / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(dict(winner=winner, rolling_results=pooled, final_2026=final), indent=2), flush=True)

if __name__ == '__main__':
    main()
