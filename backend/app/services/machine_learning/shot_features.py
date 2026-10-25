"""Experimental shot features derived strictly from previously completed fixtures."""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from app.services.machine_learning.historical_match_model import FEATURE_COLUMNS, HistoricalMatchModel

MATCH_KEYS = ["league", "match_date", "home_team", "away_team"]
SHOT_COLUMNS = [f"{side}_{name}_{window}" for side in ("home", "away") for window in (5, 10)
                for name in ("shots_for", "shots_against", "shot_difference", "shot_observations")]
TARGET_COLUMNS = [f"{side}_{name}_{window}" for side in ("home", "away") for window in (5, 10)
                  for name in ("sot_for", "sot_against", "sot_difference", "sot_observations")]
QUALITY_COLUMNS = [f"{side}_shot_accuracy_{direction}_10" for side in ("home", "away") for direction in ("for", "against")]
SHOT_VARIANTS = {"baseline": [], "shots": SHOT_COLUMNS, "shots_on_target": TARGET_COLUMNS,
                 "shots_combined": SHOT_COLUMNS + TARGET_COLUMNS + QUALITY_COLUMNS}
EXPERIMENT_COLUMNS = FEATURE_COLUMNS + SHOT_VARIANTS["shots_combined"]


class ShotFeatureModel(HistoricalMatchModel):
    def __init__(self, historical_dir=None):
        super().__init__(historical_dir)
        self.shot_history = defaultdict(lambda: deque(maxlen=10))
        self.match_statistics = {}
        self.stat_quality = {}

    def load_matches(self):
        matches = super().load_matches()
        statistics = []
        invalid = 0
        for path in sorted(self.historical_dir.glob("*.csv")):
            raw = pd.read_csv(path, usecols=lambda col: col in {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "HS", "AS", "HST", "AST"}, low_memory=False)
            if not {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}.issubset(raw):
                continue
            league, _ = path.stem.rsplit("_", 1)
            dates = pd.to_datetime(raw.Date, format="%d/%m/%Y", errors="coerce")
            missing = dates.isna()
            dates.loc[missing] = pd.to_datetime(raw.loc[missing, "Date"], format="%d/%m/%y", errors="coerce")
            final_scores = raw[["FTHG", "FTAG"]].apply(pd.to_numeric, errors="coerce")
            valid = dates.notna() & raw.HomeTeam.notna() & raw.AwayTeam.notna() & final_scores.notna().all(axis=1)
            frame = pd.DataFrame({"league": league, "match_date": dates,
                                  "home_team": raw.HomeTeam, "away_team": raw.AwayTeam})
            for name in ("HS", "AS", "HST", "AST"):
                values = pd.to_numeric(raw[name], errors="coerce") if name in raw else pd.Series(np.nan, index=raw.index)
                invalid_values = values.notna() & ((values < 0) | (values % 1 != 0) | ~np.isfinite(values))
                invalid += int((invalid_values & valid).sum())
                frame[name] = values.mask(invalid_values)
            for total, target in (("HS", "HST"), ("AS", "AST")):
                inconsistent = frame[total].notna() & frame[target].notna() & (frame[target] > frame[total])
                invalid += int((inconsistent & valid).sum())
                frame.loc[inconsistent, [total, target]] = np.nan
            statistics.append(frame[valid])
        joined = matches.merge(pd.concat(statistics, ignore_index=True), on=MATCH_KEYS, how="left", validate="one_to_one", sort=False)
        self.match_statistics = {(row.league, pd.Timestamp(row.match_date), row.home_team, row.away_team): (row.HS, row.AS, row.HST, row.AST)
                                 for row in joined.itertuples()}
        self.stat_quality = {"matches": len(joined), "invalid_statistic_entries_masked": invalid,
                             "complete_shot_pairs": int(joined[["HS", "AS"]].notna().all(axis=1).sum()),
                             "complete_target_pairs": int(joined[["HST", "AST"]].notna().all(axis=1).sum())}
        return matches

    def build_training_data(self):
        self.shot_history = defaultdict(lambda: deque(maxlen=10))
        _, target = super().build_training_data()
        frame = pd.DataFrame([{**row["features"], "league": row["league"]} for row in self.historical_examples], columns=EXPERIMENT_COLUMNS)
        if np.isinf(frame.drop(columns="league").to_numpy()).any():
            raise ValueError("Infinite shot feature")
        return frame, target

    def _update_states(self, league, home_team, away_team, home_goals, away_goals, match_date):
        values = self.match_statistics.get((league, pd.Timestamp(match_date), home_team, away_team), (np.nan,) * 4)
        hs, away_shots, hst, ast = values
        self.shot_history[self._state_key(league, home_team)].append((hs, away_shots, hst, ast))
        self.shot_history[self._state_key(league, away_team)].append((away_shots, hs, ast, hst))
        super()._update_states(league, home_team, away_team, home_goals, away_goals, match_date)

    def _features(self, league, home_team, away_team, match_date=None):
        features = super()._features(league, home_team, away_team, match_date)
        for side, team in (("home", home_team), ("away", away_team)):
            history = list(self.shot_history[self._state_key(league, team)])
            for window in (5, 10):
                recent = history[-window:]
                for prefix, first, second in (("shots", 0, 1), ("sot", 2, 3)):
                    observed = [(row[first], row[second]) for row in recent if np.isfinite(row[first]) and np.isfinite(row[second])]
                    features[f"{side}_{'shot' if prefix == 'shots' else 'sot'}_observations_{window}"] = len(observed)
                    for label, index in (("for", 0), ("against", 1)):
                        features[f"{side}_{prefix}_{label}_{window}"] = float(np.mean([row[index] for row in observed])) if observed else np.nan
                    features[f"{side}_{'shot' if prefix == 'shots' else 'sot'}_difference_{window}"] = float(np.mean([row[0] - row[1] for row in observed])) if observed else np.nan
            for direction, total, target in (("for", 0, 2), ("against", 1, 3)):
                observed = [row for row in history if np.isfinite(row[total]) and np.isfinite(row[target])]
                denominator = sum(row[total] for row in observed)
                features[f"{side}_shot_accuracy_{direction}_10"] = sum(row[target] for row in observed) / denominator if denominator else np.nan
        return features
