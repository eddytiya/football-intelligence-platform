"""Selection and final evaluation on disjoint date blocks; fixed-model backtests."""
from datetime import datetime, timezone
import hashlib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss, mean_absolute_error, confusion_matrix
from app.core.paths import REPORTS_DIR
from app.services.machine_learning.temporal_protocol import PROTOCOL_VERSION, chronological_splits


def goal_model(model):
    return Pipeline([('features', model._preprocessor(dense=True)), ('model', CatBoostRegressor(
        loss_function='MAE', iterations=300, depth=6, learning_rate=.05, l2_leaf_reg=5,
        verbose=False, random_seed=42, thread_count=4, allow_writing_files=False))])


def train_chronological(model):
    features, target = model.build_training_data()
    dates = pd.to_datetime([item['match_date'] for item in model.historical_examples])
    train, validation, test = chronological_splits(dates)
    comparisons = []
    for name, candidate in model._candidate_models(dates[train]).items():
        candidate.fit(features.iloc[train], target.iloc[train])
        probability = candidate.predict_proba(features.iloc[validation])
        comparisons.append({'model': name,
            'accuracy': float(accuracy_score(target.iloc[validation], candidate.predict(features.iloc[validation]))),
            'balanced_accuracy': float(balanced_accuracy_score(target.iloc[validation], candidate.predict(features.iloc[validation]))),
            'log_loss': float(log_loss(target.iloc[validation], probability, labels=[0, 1, 2]))})
    comparisons.sort(key=lambda row: (row['log_loss'], -row['balanced_accuracy']))
    selected = comparisons[0]['model']
    development = np.concatenate([train, validation])
    evaluation = model._candidate_models(dates[development])[selected]
    evaluation.fit(features.iloc[development], target.iloc[development])
    home, away = goal_model(model), goal_model(model)
    home.fit(features.iloc[development], model.home_goal_targets.iloc[development])
    away.fit(features.iloc[development], model.away_goal_targets.iloc[development])
    ml = evaluation.predict_proba(features.iloc[test])
    hx, ax = home.predict(features.iloc[test]), away.predict(features.iloc[test])
    probabilities = []
    for row, p, h, a in zip(features.iloc[test].to_dict('records'), ml, hx, ax):
        combined = model._ensemble_probabilities(dict(zip(evaluation.classes_, p)),
            model._elo_outcome_probabilities(row), model._poisson_outcome_probabilities(h, a))
        probabilities.append([combined[index] for index in (0, 1, 2)])
    guesses = np.asarray(probabilities).argmax(axis=1)
    score = {'accuracy': float(accuracy_score(target.iloc[test], guesses)),
             'balanced_accuracy': float(balanced_accuracy_score(target.iloc[test], guesses)),
             'log_loss': float(log_loss(target.iloc[test], probabilities, labels=[0, 1, 2]))}
    metrics = {**score, 'evaluation_protocol': 'chronological_train_selection_test_v1',
        'selection_training_matches': len(train), 'training_matches': len(development),
        'validation_matches': len(validation), 'test_matches': len(test),
        'selection_start': str(dates[validation[0]].date()), 'test_start': str(dates[test[0]].date()),
        'test_end': str(dates[test[-1]].date()), 'selected_model': selected, 'model_comparison': comparisons,
        'expected_goals_mae': {'home': float(mean_absolute_error(model.home_goal_targets.iloc[test], hx)),
                               'away': float(mean_absolute_error(model.away_goal_targets.iloc[test], ax))},
        'website_ensemble': {**score, 'name': '50% outcome classifier + 25% Elo + 25% goal-model Poisson',
            'evaluation_protocol': 'untouched_chronological_test', 'test_start': str(dates[test[0]].date()),
            'test_matches': len(test), 'confusion_matrix_away_draw_home': confusion_matrix(target.iloc[test], guesses, labels=[0,1,2]).tolist()}}
    export = features.iloc[test][['league']].reset_index(drop=True)
    export['match_date'], export['actual'] = dates[test], target.iloc[test].to_numpy()
    export[['away_probability', 'draw_probability', 'home_probability']] = probabilities
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    export.to_csv(REPORTS_DIR / 'website_ensemble_validation.csv', index=False)
    # Deploy only after metrics are frozen. This full-history model never scores its own past.
    model.pipeline = model._candidate_models(dates)[selected]
    model.pipeline.fit(features, target)
    model.home_goals_pipeline, model.away_goals_pipeline = goal_model(model), goal_model(model)
    model.home_goals_pipeline.fit(features, model.home_goal_targets)
    model.away_goals_pipeline.fit(features, model.away_goal_targets)
    model.leakage_protocol_version = PROTOCOL_VERSION
    return metrics


def fit_walk_forward(model, cutoff):
    """Fixed, predeclared estimators; no model selection using a later period."""
    features, target = model.build_training_data(before_date=cutoff)
    if len(features) < 300 or target.nunique() != 3:
        raise ValueError('Insufficient pre-cutoff history for an honest historical backtest.')
    model.pipeline = Pipeline([('features', model._preprocessor(scale_numeric=True)),
        ('model', LogisticRegression(max_iter=1000, C=1, random_state=42))])
    model.home_goals_pipeline = Pipeline([('features', model._preprocessor(dense=True, scale_numeric=True)),
        ('model', PoissonRegressor(alpha=1, max_iter=500))])
    model.away_goals_pipeline = Pipeline([('features', model._preprocessor(dense=True, scale_numeric=True)),
        ('model', PoissonRegressor(alpha=1, max_iter=500))])
    model.pipeline.fit(features, target)
    model.home_goals_pipeline.fit(features, model.home_goal_targets)
    model.away_goals_pipeline.fit(features, model.away_goal_targets)
    digest = hashlib.sha256(pd.util.hash_pandas_object(features, index=True).values.tobytes()
        + target.to_numpy().tobytes()).hexdigest()[:16]
    model.model_version = f'walk-forward-v1-{cutoff}-{digest}'
    model.leakage_protocol_version = PROTOCOL_VERSION
    return model
