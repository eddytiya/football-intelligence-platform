"""Lagged shot context: opponent strength and relevant home/away venue history."""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from app.services.machine_learning.historical_match_model import HistoricalMatchModel
from app.services.machine_learning.shot_features import ShotFeatureModel, EXPERIMENT_COLUMNS

ADJUSTED_COLUMNS = [f"{side}_{kind}_{window}" for side in ("home", "away") for window in (5, 10)
                    for kind in ("adjusted_shots_for", "adjusted_shots_against", "adjusted_sot_for", "adjusted_sot_against", "adjusted_shot_observations", "adjusted_sot_observations")]
VENUE_COLUMNS = [f"{side}_venue_{kind}_{window}" for side in ("home", "away") for window in (5, 10)
                 for kind in ("shots_for", "shots_against", "sot_for", "sot_against", "shot_observations", "sot_observations")]
CONTEXT_COLUMNS = EXPERIMENT_COLUMNS + ADJUSTED_COLUMNS + VENUE_COLUMNS


def summarise_history(history, side, prefix, window):
    result = {}
    recent = list(history)[-window:]
    for label, first, second in (("shots", 0, 1), ("sot", 2, 3)):
        valid = [row for row in recent if np.isfinite(row[first]) and np.isfinite(row[second])]
        for direction, index in (("for", first), ("against", second)):
            result[f"{side}_{prefix}{label}_{direction}_{window}"] = float(np.mean([row[index] for row in valid])) if valid else np.nan
        result[f"{side}_{prefix}{'shot' if label == 'shots' else 'sot'}_observations_{window}"] = len(valid)
    return result


class ShotContextModel(ShotFeatureModel):
    def __init__(self, historical_dir=None):
        super().__init__(historical_dir)
        self.adjusted_history = defaultdict(lambda: deque(maxlen=10))
        self.venue_history = defaultdict(lambda: deque(maxlen=10))
        self.league_shots = defaultdict(lambda: [0., 0, 0., 0])
        self.daily_priors = {}

    def build_training_data(self):
        self.shot_history = defaultdict(lambda: deque(maxlen=10))
        self.adjusted_history = defaultdict(lambda: deque(maxlen=10))
        self.venue_history = defaultdict(lambda: deque(maxlen=10))
        self.league_shots = defaultdict(lambda: [0., 0, 0., 0])
        self.daily_priors = {}
        _, target = HistoricalMatchModel.build_training_data(self)
        frame = pd.DataFrame([{**row["features"], "league": row["league"]} for row in self.historical_examples], columns=CONTEXT_COLUMNS)
        if np.isinf(frame.drop(columns="league").to_numpy()).any():
            raise ValueError("Infinite context features")
        return frame, target

    def adjusted_record(self, league, opponent_key, observed, priors=None):
        previous = list(self.shot_history[opponent_key])
        league_total, league_n, target_total, target_n = priors if priors is not None else self.league_shots[league]
        means = (league_total / league_n if league_n else 13., target_total / target_n if target_n else 4.)
        adjusted = []
        for column, value in enumerate(observed):
            # Attacking shots are compared with the opponent's pre-match defensive
            # record; conceded shots are compared with its attacking record.
            opposite = {0: 1, 1: 0, 2: 3, 3: 2}[column]
            valid = [row[opposite] for row in previous if np.isfinite(row[opposite])]
            mean = means[0 if column < 2 else 1]
            expected = (sum(valid) + 5 * mean) / (len(valid) + 5)
            adjusted.append(value * mean / max(expected, .1) if np.isfinite(value) else np.nan)
        return tuple(adjusted)

    def _update_states(self, league, home_team, away_team, home_goals, away_goals, match_date):
        home, away = self._state_key(league, home_team), self._state_key(league, away_team)
        hs, away_shots, hst, ast = self.match_statistics.get((league, pd.Timestamp(match_date), home_team, away_team), (np.nan,) * 4)
        home_row, away_row = (hs, away_shots, hst, ast), (away_shots, hs, ast, hst)
        # Compute BOTH normalisations before appending either current record.
        day_key = (league, pd.Timestamp(match_date).normalize())
        priors = self.daily_priors.setdefault(day_key, tuple(self.league_shots[league]))
        home_adjusted = self.adjusted_record(league, away, home_row, priors)
        away_adjusted = self.adjusted_record(league, home, away_row, priors)
        self.adjusted_history[home].append(home_adjusted)
        self.adjusted_history[away].append(away_adjusted)
        self.venue_history[(home, "home")].append(home_row)
        self.venue_history[(away, "away")].append(away_row)
        for value in (hs, away_shots):
            if np.isfinite(value):
                self.league_shots[league][0] += value
                self.league_shots[league][1] += 1
        for value in (hst, ast):
            if np.isfinite(value):
                self.league_shots[league][2] += value
                self.league_shots[league][3] += 1
        super()._update_states(league, home_team, away_team, home_goals, away_goals, match_date)

    def _features(self, league, home_team, away_team, match_date=None):
        features = super()._features(league, home_team, away_team, match_date)
        for side, team in (("home", home_team), ("away", away_team)):
            key = self._state_key(league, team)
            for window in (5, 10):
                features.update(summarise_history(self.adjusted_history[key], side, "adjusted_", window))
                features.update(summarise_history(self.venue_history[(key, side)], side, "venue_", window))
        return features
