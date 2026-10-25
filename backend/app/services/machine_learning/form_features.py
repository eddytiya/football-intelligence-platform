"""Experimental pre-match features; does not change the active v2 feature schema."""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel


OPPONENT_COLUMNS = [f"{side}_{name}_{window}" for side in ("home", "away")
                    for window in (5, 10) for name in ("opponent_adjusted_result", "opponent_elo")]
OPPONENT_COLUMNS += ["opponent_adjusted_form_gap_5"]
RECENT_COLUMNS = [f"{side}_{name}_{window}" for side in ("home", "away") for window in (5, 10)
                  for name in ("recent_scored", "recent_conceded", "attack_change", "defence_change")]
RECENT_COLUMNS += [f"{side}_{name}" for side in ("home", "away")
                   for name in ("recent_clean_sheet_rate_5", "recent_failed_to_score_rate_5", "recent_matches_available")]
BALANCE_COLUMNS = ["absolute_elo_gap_with_home_advantage", "absolute_season_ppg_gap",
                   "absolute_form_ppg_gap_5", "absolute_recent_goal_difference_gap_5",
                   "season_goal_rate_gap", "combined_recent_goal_rate_5",
                   "home_recent_draw_rate_10", "away_recent_draw_rate_10"]
FEATURE_GROUPS = {"opponent_adjusted": OPPONENT_COLUMNS, "recent_strength": RECENT_COLUMNS,
                  "match_balance": BALANCE_COLUMNS}
EXPERIMENT_COLUMNS = FEATURE_COLUMNS + OPPONENT_COLUMNS + RECENT_COLUMNS + BALANCE_COLUMNS


class FormFeatureModel(HistoricalMatchModel):
    def __init__(self, historical_dir=None):
        super().__init__(historical_dir)
        self.opponent_history = defaultdict(lambda: deque(maxlen=10))

    def build_training_data(self):
        self.opponent_history = defaultdict(lambda: deque(maxlen=10))
        _, target = super().build_training_data()
        frame = pd.DataFrame([{**row["features"], "league": row["league"]}
                              for row in self.historical_examples], columns=EXPERIMENT_COLUMNS)
        if not np.isfinite(frame.drop(columns="league").to_numpy()).all():
            raise ValueError("Nonfinite experimental features")
        return frame, target

    def _update_states(self, league, home_team, away_team, home_goals, away_goals, match_date):
        home_key, away_key = self._state_key(league, home_team), self._state_key(league, away_team)
        home_elo, away_elo = self.states[home_key].elo, self.states[away_key].elo
        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo - 70) / 400))
        actual_home = 1. if home_goals > away_goals else .5 if home_goals == away_goals else 0.
        self.opponent_history[home_key].append((actual_home - expected_home, away_elo))
        self.opponent_history[away_key].append(((1 - actual_home) - (1 - expected_home), home_elo))
        super()._update_states(league, home_team, away_team, home_goals, away_goals, match_date)

    def _features(self, league, home_team, away_team, match_date=None):
        features = super()._features(league, home_team, away_team, match_date)
        recent_goals = {}
        for side, team in (("home", home_team), ("away", away_team)):
            key = self._state_key(league, team)
            state = self.states[key]
            scorelines = list(state.recent_scorelines)
            opponent_history = list(self.opponent_history[key])
            for window in (5, 10):
                opponents = opponent_history[-window:]
                features[f"{side}_opponent_adjusted_result_{window}"] = float(np.mean([r[0] for r in opponents])) if opponents else 0.
                features[f"{side}_opponent_elo_{window}"] = float(np.mean([r[1] for r in opponents])) if opponents else 1500.
                scores = scorelines[-window:]
                scored = float(np.mean([r[0] for r in scores])) if scores else 0.
                conceded = float(np.mean([r[1] for r in scores])) if scores else 0.
                features[f"{side}_recent_scored_{window}"] = scored
                features[f"{side}_recent_conceded_{window}"] = conceded
                # Avoid declaring momentum from an empty new-season denominator.
                features[f"{side}_attack_change_{window}"] = scored - features[f"{side}_attack_strength"] if state.games else 0.
                features[f"{side}_defence_change_{window}"] = conceded - features[f"{side}_defence_strength"] if state.games else 0.
            five = scorelines[-5:]
            features[f"{side}_recent_clean_sheet_rate_5"] = sum(r[1] == 0 for r in five) / len(five) if five else 0.
            features[f"{side}_recent_failed_to_score_rate_5"] = sum(r[0] == 0 for r in five) / len(five) if five else 0.
            features[f"{side}_recent_matches_available"] = len(scorelines)
            features[f"{side}_recent_draw_rate_10"] = sum(r[0] == r[1] for r in scorelines) / len(scorelines) if scorelines else 0.
            recent_goals[side] = features[f"{side}_recent_scored_5"] + features[f"{side}_recent_conceded_5"]
        features.update({
            "opponent_adjusted_form_gap_5": features["home_opponent_adjusted_result_5"] - features["away_opponent_adjusted_result_5"],
            "absolute_elo_gap_with_home_advantage": abs(features["elo_difference"] + 70),
            "absolute_season_ppg_gap": abs(features["home_points_per_game"] - features["away_points_per_game"]),
            "absolute_form_ppg_gap_5": abs(features["home_form_points_5"] - features["away_form_points_5"]),
            "absolute_recent_goal_difference_gap_5": abs(features["home_form_goal_difference_5"] - features["away_form_goal_difference_5"]),
            "season_goal_rate_gap": abs((features["home_attack_strength"] + features["away_defence_strength"]
                                          - features["away_attack_strength"] - features["home_defence_strength"]) / 2),
            "combined_recent_goal_rate_5": (recent_goals["home"] + recent_goals["away"]) / 2,
        })
        return features
