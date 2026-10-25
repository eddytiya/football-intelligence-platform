"""Train a leakage-safe match-outcome model from football-data.co.uk CSV files.

Features are calculated before each match from only earlier matches in the
same competition.  This module deliberately does not use final scores or
betting odds as input features.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier, CatBoostRegressor
from math import exp, factorial

from app.core.paths import MODELS_DIR, REPORTS_DIR
from app.services.machine_learning.team_identity import identity_key
from app.services.machine_learning.temporal_protocol import PROTOCOL_VERSION, calibration_folds, chronological_splits

FEATURE_SCHEMA_VERSION = 3


FEATURE_COLUMNS = [
    "league", "home_elo", "away_elo", "elo_difference",
    "home_games", "away_games", "home_points_per_game", "away_points_per_game",
    "home_goal_difference_per_game", "away_goal_difference_per_game",
    "home_attack_strength", "away_attack_strength", "home_defence_strength", "away_defence_strength",
    "home_form_points_5", "away_form_points_5", "home_form_points_10", "away_form_points_10",
    "home_form_goal_difference_5", "away_form_goal_difference_5",
    "home_league_position", "away_league_position", "league_position_difference",
    "home_rest_days", "away_rest_days", "rest_days_difference",
    "home_home_points_per_game", "away_away_points_per_game",
    "h2h_matches", "home_h2h_points_per_game", "home_h2h_goal_difference_per_game",
]
NUMERIC_FEATURES = [column for column in FEATURE_COLUMNS if column != "league"]


def normalise_team_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


@dataclass
class TeamState:
    games: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    elo: float = 1500.0
    recent_results: deque = field(default_factory=lambda: deque(maxlen=10))
    recent_goal_differences: deque = field(default_factory=lambda: deque(maxlen=10))
    recent_scorelines: deque = field(default_factory=lambda: deque(maxlen=5))
    home_games: int = 0
    home_points: int = 0
    away_games: int = 0
    away_points: int = 0
    last_match_date: datetime | None = None


class HistoricalMatchModel:
    """Produces a chronological dataset, trains a model, and predicts fixtures."""

    # Known provider-name differences in the scheduled feed versus historical CSVs.
    TEAM_ALIASES = {
        "nec": "nijmegen", "telstar1963": "telstar", "willemiitilburg": "willemii",
        "psv": "psveindhoven", "fortunasittard": "forsittard", "az": "azalkmaar", "adodenhaag": "denhaag",
        "csmaritimo": "maritimo", "casapiaac": "casapia", "vitoriasc": "guimaraes",
        "fcarouca": "arouca", "cfestreladaamadora": "estrela",
        "sportingclubedeportugal": "splisbon",
        "sccambuurleeuwarden": "cambuur", "sbvexcelsior": "excelsior",
    }

    def __init__(self, historical_dir: Path | None = None):
        self.historical_dir = historical_dir or MODELS_DIR.parents[0] / "data" / "raw" / "historical"
        self.states: dict[str, TeamState] = defaultdict(TeamState)
        self.known_teams: dict[str, set[str]] = defaultdict(set)
        self.head_to_head: dict[tuple[str, str, str], deque] = defaultdict(lambda: deque(maxlen=10))
        self.pipeline: Pipeline | None = None
        self.home_goals_pipeline: Pipeline | None = None
        self.away_goals_pipeline: Pipeline | None = None
        # Kept as pre-match snapshots so the API can find genuinely similar
        # historical fixtures without inspecting the outcome of the selected
        # fixture itself.
        self.historical_examples: list[dict] = []
        self.league_seasons: dict[str, int] = {}
        self.league_members: dict[str, set[str]] = {}
        self.feature_schema_version = FEATURE_SCHEMA_VERSION
        self.model_version = f"historical-season-v{FEATURE_SCHEMA_VERSION}"
        self.training_data_through = None
        self.leakage_protocol_version = None

    def _start_season(self, league: str, season: int, members: set[str]) -> None:
        if self.league_seasons.get(league) == season:
            return
        for key, old in list(self.states.items()):
            if key.startswith(f"{league}:"):
                self.states[key] = TeamState(
                    elo=old.elo, recent_results=deque(old.recent_results, maxlen=10),
                    recent_goal_differences=deque(old.recent_goal_differences, maxlen=10),
                    recent_scorelines=deque(old.recent_scorelines, maxlen=5), last_match_date=old.last_match_date,
                )
        self.league_seasons[league] = season
        self.league_members[league] = {self._state_key(league, team) for team in members}

    @staticmethod
    def _target(home_goals: int, away_goals: int) -> int:
        return 2 if home_goals > away_goals else 1 if home_goals == away_goals else 0

    @staticmethod
    def _state_key(league: str, team: str) -> str:
        return f"{league}:{normalise_team_name(team)}"

    def _league_position(self, league: str, team_key: str) -> int:
        table = [
            (key, state) for key, state in self.states.items()
            if key in self.league_members.get(league, set())
        ]
        for key in sorted(self.league_members.get(league, set())):
            if key not in self.states:
                table.append((key, TeamState()))
        table.sort(key=lambda item: (
            -item[1].points,
            -(item[1].goals_for - item[1].goals_against),
            -item[1].goals_for,
            -item[1].elo,
            item[0],
        ))
        return next((index for index, (key, _) in enumerate(table, start=1) if key == team_key), len(table) + 1)

    def _h2h_stats(self, league: str, home_key: str, away_key: str) -> tuple[int, float, float]:
        key = (league, *sorted((home_key, away_key)))
        records = self.head_to_head[key]
        points, goal_difference = 0, 0
        for prior_home, prior_away, home_goals, away_goals in records:
            if prior_home == home_key:
                goals_for, goals_against = home_goals, away_goals
            else:
                goals_for, goals_against = away_goals, home_goals
            points += 3 if goals_for > goals_against else 1 if goals_for == goals_against else 0
            goal_difference += goals_for - goals_against
        games = len(records)
        return games, points / games if games else 0.0, goal_difference / games if games else 0.0

    def _features(self, league: str, home_team: str, away_team: str, match_date: datetime | None = None) -> dict:
        home_key, away_key = self._state_key(league, home_team), self._state_key(league, away_team)
        home, away = self.states[home_key], self.states[away_key]

        def per_game(value: float, games: int) -> float:
            return value / games if games else 0.0

        h2h_matches, home_h2h_ppg, home_h2h_gd = self._h2h_stats(league, home_key, away_key)
        home_rest = max(0, (match_date - home.last_match_date).days) if match_date and home.last_match_date else 7
        away_rest = max(0, (match_date - away.last_match_date).days) if match_date and away.last_match_date else 7
        home_position, away_position = self._league_position(league, home_key), self._league_position(league, away_key)
        return {
            "league": league,
            "home_elo": home.elo,
            "away_elo": away.elo,
            "elo_difference": home.elo - away.elo,
            "home_games": home.games,
            "away_games": away.games,
            "home_points_per_game": per_game(home.points, home.games),
            "away_points_per_game": per_game(away.points, away.games),
            "home_goal_difference_per_game": per_game(home.goals_for - home.goals_against, home.games),
            "away_goal_difference_per_game": per_game(away.goals_for - away.goals_against, away.games),
            "home_attack_strength": per_game(home.goals_for, home.games),
            "away_attack_strength": per_game(away.goals_for, away.games),
            "home_defence_strength": per_game(home.goals_against, home.games),
            "away_defence_strength": per_game(away.goals_against, away.games),
            "home_form_points_5": per_game(sum(list(home.recent_results)[-5:]), min(5, len(home.recent_results))),
            "away_form_points_5": per_game(sum(list(away.recent_results)[-5:]), min(5, len(away.recent_results))),
            "home_form_points_10": per_game(sum(home.recent_results), len(home.recent_results)),
            "away_form_points_10": per_game(sum(away.recent_results), len(away.recent_results)),
            "home_form_goal_difference_5": per_game(sum(list(home.recent_goal_differences)[-5:]), min(5, len(home.recent_goal_differences))),
            "away_form_goal_difference_5": per_game(sum(list(away.recent_goal_differences)[-5:]), min(5, len(away.recent_goal_differences))),
            "home_league_position": home_position,
            "away_league_position": away_position,
            "league_position_difference": away_position - home_position,
            "home_rest_days": min(home_rest, 30), "away_rest_days": min(away_rest, 30),
            "rest_days_difference": min(home_rest, 30) - min(away_rest, 30),
            "home_home_points_per_game": per_game(home.home_points, home.home_games),
            "away_away_points_per_game": per_game(away.away_points, away.away_games),
            "h2h_matches": h2h_matches,
            "home_h2h_points_per_game": home_h2h_ppg,
            "home_h2h_goal_difference_per_game": home_h2h_gd,
        }

    def _update_states(self, league: str, home_team: str, away_team: str, home_goals: int, away_goals: int, match_date: datetime) -> None:
        home = self.states[self._state_key(league, home_team)]
        away = self.states[self._state_key(league, away_team)]
        home_points = 3 if home_goals > away_goals else 1 if home_goals == away_goals else 0
        away_points = 3 if away_goals > home_goals else 1 if home_goals == away_goals else 0
        expected_home = 1 / (1 + 10 ** ((away.elo - (home.elo + 70)) / 400))
        actual_home = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
        adjustment = 20 * (actual_home - expected_home)

        for state, goals_for, goals_against, points in (
            (home, home_goals, away_goals, home_points),
            (away, away_goals, home_goals, away_points),
        ):
            state.games += 1
            state.points += points
            state.goals_for += goals_for
            state.goals_against += goals_against
            state.recent_results.append(points)
            state.recent_goal_differences.append(goals_for - goals_against)
            state.recent_scorelines.append((goals_for, goals_against))
        home.elo += adjustment
        away.elo -= adjustment
        home.home_games += 1
        home.home_points += home_points
        away.away_games += 1
        away.away_points += away_points
        home.last_match_date = match_date
        away.last_match_date = match_date
        self.head_to_head[(league, *sorted((self._state_key(league, home_team), self._state_key(league, away_team))))].append(
            (self._state_key(league, home_team), self._state_key(league, away_team), home_goals, away_goals)
        )

    def load_matches(self) -> pd.DataFrame:
        records = []
        for file_path in sorted(self.historical_dir.glob("*.csv")):
            league, season = file_path.stem.rsplit("_", 1)
            frame = pd.read_csv(file_path, usecols=lambda col: col in {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}, low_memory=False)
            if not {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}.issubset(frame.columns):
                continue
            # The archive contains both four-digit and two-digit years. Parse
            # each explicitly rather than relying on slow, ambiguous inference.
            frame["match_date"] = pd.to_datetime(frame["Date"], format="%d/%m/%Y", errors="coerce")
            unresolved_dates = frame["match_date"].isna()
            frame.loc[unresolved_dates, "match_date"] = pd.to_datetime(
                frame.loc[unresolved_dates, "Date"], format="%d/%m/%y", errors="coerce",
            )
            frame["home_goals"] = pd.to_numeric(frame["FTHG"], errors="coerce")
            frame["away_goals"] = pd.to_numeric(frame["FTAG"], errors="coerce")
            frame = frame.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "home_goals", "away_goals"])
            frame = frame[(frame.home_goals >= 0) & (frame.away_goals >= 0)
                          & (frame.home_goals % 1 == 0) & (frame.away_goals % 1 == 0)]
            for row in frame.itertuples(index=False):
                records.append({
                    "match_date": row.match_date, "league": league, "season": int(season),
                    "home_team": str(row.HomeTeam), "away_team": str(row.AwayTeam),
                    "home_goals": int(row.home_goals), "away_goals": int(row.away_goals),
                })
        matches = pd.DataFrame(records)
        if matches.empty:
            raise ValueError(f"No valid historical matches found in {self.historical_dir}")
        matches = matches.sort_values(["match_date", "league", "season"], kind="stable").reset_index(drop=True)
        if matches.duplicated(["league", "match_date", "home_team", "away_team"]).any():
            raise ValueError("Duplicate fixtures in historical archive; review before training")
        return matches

    def build_training_data(self, before_date=None) -> tuple[pd.DataFrame, pd.Series]:
        self.states = defaultdict(TeamState)
        self.known_teams = defaultdict(set)
        self.head_to_head = defaultdict(lambda: deque(maxlen=10))
        self.historical_examples = []
        self.league_seasons = {}
        self.league_members = {}
        rows, targets, home_goal_targets, away_goal_targets = [], [], [], []
        matches = self.load_matches()
        cutoff = pd.Timestamp(before_date or datetime.now(timezone.utc).date()).tz_localize(None).normalize()
        matches = matches[matches.match_date < cutoff]
        if matches.empty:
            raise ValueError('No completed historical days precede the training cutoff.')
        self.training_data_through = str(matches.match_date.max().date())
        memberships = defaultdict(set)
        # Every fixture on the same calendar day receives features from the
        # same pre-kickoff state; no result from an earlier same-day fixture
        # can leak into another fixture's feature vector.
        for _, match_day in matches.groupby("match_date", sort=True):
            day_matches = list(match_day.itertuples(index=False))
            for match in day_matches:
                memberships[(match.league, match.season)].update({match.home_team, match.away_team})
            for match in day_matches:
                self._start_season(match.league, match.season, memberships[(match.league, match.season)])
                self.league_members[match.league] = {self._state_key(match.league, team) for team in memberships[(match.league, match.season)]}
            for match in day_matches:
                features = self._features(match.league, match.home_team, match.away_team, match.match_date)
                rows.append(features)
                targets.append(self._target(match.home_goals, match.away_goals))
                home_goal_targets.append(match.home_goals)
                away_goal_targets.append(match.away_goals)
                self.historical_examples.append({
                    "match_date": match.match_date.isoformat(), "league": match.league, "season": int(match.season),
                    "home_team": match.home_team, "away_team": match.away_team,
                    "home_goals": int(match.home_goals), "away_goals": int(match.away_goals),
                    "result": self._target(match.home_goals, match.away_goals),
                    "features": {key: float(value) for key, value in features.items() if key != "league"},
                })
                self.known_teams[match.league].update({normalise_team_name(match.home_team), normalise_team_name(match.away_team)})
            for match in day_matches:
                self._update_states(match.league, match.home_team, match.away_team, match.home_goals, match.away_goals, match.match_date)
        self.home_goal_targets = pd.Series(home_goal_targets, name="home_goals")
        self.away_goal_targets = pd.Series(away_goal_targets, name="away_goals")
        return pd.DataFrame(rows, columns=FEATURE_COLUMNS), pd.Series(targets, name="match_result")

    @staticmethod
    def _preprocessor(dense: bool = False, scale_numeric: bool = False) -> ColumnTransformer:
        preprocessing = ColumnTransformer([
            ("league", OneHotEncoder(handle_unknown="ignore", sparse_output=not dense), ["league"]),
            ("numeric", Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler() if scale_numeric else "passthrough"),
            ]), NUMERIC_FEATURES),
        ])
        return preprocessing

    @classmethod
    def _candidate_models(cls, dates) -> dict[str, Pipeline]:
        return {
            "calibrated_logistic_regression": Pipeline([
                ("model", CalibratedClassifierCV(
                    estimator=Pipeline([
                        ("features", cls._preprocessor(scale_numeric=True)),
                        ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
                    ]),
                    # Calibration must only learn from matches that happened
                    # before the validation fold. Random folds leak future
                    # football form into past forecasts.
                    method="sigmoid", cv=calibration_folds(dates),
                )),
            ]),
            "lightgbm": Pipeline([
                ("features", cls._preprocessor()),
                ("model", LGBMClassifier(
                    objective="multiclass", num_class=3, n_estimators=250,
                    learning_rate=0.04, num_leaves=31, min_child_samples=30,
                    colsample_bytree=0.85, reg_lambda=1.0, n_jobs=-1,
                    random_state=42, verbosity=-1,
                )),
            ]),
            "catboost": Pipeline([
                ("features", cls._preprocessor(dense=True)),
                ("model", CatBoostClassifier(
                    loss_function="MultiClass", iterations=250, depth=6,
                    learning_rate=0.05, l2_leaf_reg=5, verbose=False,
                    random_seed=42, thread_count=4, allow_writing_files=False,
                )),
            ]),
        }

    def train(self, artifact_path: Path | None = None) -> dict:
        from app.services.machine_learning.temporal_training import train_chronological
        metrics = train_chronological(self)
        artifact = {
            "pipeline": self.pipeline,
            "home_goals_pipeline": self.home_goals_pipeline,
            "away_goals_pipeline": self.away_goals_pipeline,
            # Store only standard Python containers so this artifact can be
            # loaded by the API process (rather than only by `python -m`).
            "states": {
                key: {
                    "games": state.games,
                    "points": state.points,
                    "goals_for": state.goals_for,
                    "goals_against": state.goals_against,
                    "elo": state.elo,
                    "recent_results": list(state.recent_results),
                    "recent_goal_differences": list(state.recent_goal_differences),
                    "recent_scorelines": list(state.recent_scorelines),
                    "home_games": state.home_games, "home_points": state.home_points,
                    "away_games": state.away_games, "away_points": state.away_points,
                    "last_match_date": state.last_match_date,
                }
                for key, state in self.states.items()
            },
            "head_to_head": {key: list(records) for key, records in self.head_to_head.items()},
            "known_teams": {league: sorted(teams) for league, teams in self.known_teams.items()},
            "metrics": metrics,
            "trained_at": datetime.now().isoformat(),
            "feature_columns": FEATURE_COLUMNS,
            "historical_examples": self.historical_examples,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "leakage_protocol_version": self.leakage_protocol_version,
            "training_data_through": self.training_data_through,
            "league_seasons": self.league_seasons,
            "league_members": {key: sorted(value) for key, value in self.league_members.items()},
        }
        artifact_path = artifact_path or MODELS_DIR / "historical_match_model.joblib"
        temporary = artifact_path.with_suffix(".tmp")
        joblib.dump(artifact, temporary)
        temporary.replace(artifact_path)
        return {"artifact_path": artifact_path, **metrics}

    @classmethod
    def load(cls, artifact_path: Path | None = None) -> "HistoricalMatchModel":
        """Load a portable trained artifact for prediction without retraining."""
        artifact = joblib.load(artifact_path or MODELS_DIR / "historical_match_model.joblib")
        model = cls()
        model.feature_schema_version = artifact.get("feature_schema_version", 1)
        model.leakage_protocol_version = artifact.get("leakage_protocol_version")
        model.training_data_through = artifact.get("training_data_through")
        model.model_version = f"historical-season-v{model.feature_schema_version}-{artifact.get('trained_at', 'unknown')}"
        model.league_seasons = artifact.get("league_seasons", {})
        model.league_members = {league: set(members) for league, members in artifact.get("league_members", {}).items()}
        model.pipeline = artifact["pipeline"]
        model.home_goals_pipeline = artifact.get("home_goals_pipeline")
        model.away_goals_pipeline = artifact.get("away_goals_pipeline")
        model.known_teams = defaultdict(set, {
            league: set(teams) for league, teams in artifact["known_teams"].items()
        })
        model.states = defaultdict(TeamState)
        for key, values in artifact["states"].items():
            model.states[key] = TeamState(
                games=values["games"], points=values["points"],
                goals_for=values["goals_for"], goals_against=values["goals_against"],
                elo=values["elo"], recent_results=deque(values["recent_results"], maxlen=10),
                recent_goal_differences=deque(values["recent_goal_differences"], maxlen=10),
                recent_scorelines=deque(values.get("recent_scorelines", []), maxlen=5),
                home_games=values.get("home_games", 0), home_points=values.get("home_points", 0),
                away_games=values.get("away_games", 0), away_points=values.get("away_points", 0),
                last_match_date=values.get("last_match_date"),
            )
        model.head_to_head = defaultdict(lambda: deque(maxlen=10), {
            tuple(key): deque(records, maxlen=10)
            for key, records in artifact.get("head_to_head", {}).items()
        })
        model.historical_examples = artifact.get("historical_examples", [])
        return model

    def _resolve_team(self, league: str, team_name: str) -> tuple[str, float]:
        requested = identity_key(team_name)
        requested = self.TEAM_ALIASES.get(requested, requested)
        candidates = self.known_teams.get(league, set())
        # The historical archive covers eight European leagues only. Never
        # manufacture a high-confidence match for an unsupported competition.
        if not candidates:
            return requested, 0.0
        literal = normalise_team_name(team_name)
        if literal in candidates:
            return literal, 1.0
        if requested in candidates:
            return requested, 1.0
        matches = sorted(candidate for candidate in candidates if identity_key(candidate) == requested)
        if len(matches) == 1:
            return matches[0], 1.0
        return requested, 0.0

    def predict_fixture(
        self,
        league: str,
        home_team: str,
        away_team: str,
        match_date: datetime | None = None,
    ) -> dict:
        return self.predict_fixtures([{
            "league": league, "home_team": home_team, "away_team": away_team,
            "utc_date": match_date,
        }])[0]

    @staticmethod
    def _form_summary(state: TeamState) -> dict:
        """Return a compact summary of the team's five latest recorded matches."""
        results = list(state.recent_results)[-5:]
        scorelines = list(state.recent_scorelines)[-5:]
        return {
            "matches": len(results),
            "wins": sum(result == 3 for result in results),
            "draws": sum(result == 1 for result in results),
            "losses": sum(result == 0 for result in results),
            "goals_scored": sum(score[0] for score in scorelines),
            "goals_conceded": sum(score[1] for score in scorelines),
            "clean_sheets": sum(score[1] == 0 for score in scorelines),
            "form": "".join("W" if result == 3 else "D" if result == 1 else "L" for result in results),
        }

    @staticmethod
    def _confidence(probability_by_class: dict, coverage: float) -> dict:
        ordered = sorted((float(value) for value in probability_by_class.values()), reverse=True)
        top_probability = ordered[0] if ordered else 0.0
        probability_spread = top_probability - (ordered[1] if len(ordered) > 1 else 0.0)
        if coverage >= 0.8 and top_probability >= 0.55 and probability_spread >= 0.12:
            level = "High"
        elif coverage >= 0.55 and top_probability >= 0.43 and probability_spread >= 0.04:
            level = "Medium"
        else:
            level = "Low"
        return {
            "level": level,
            "top_probability": round(top_probability, 4),
            "probability_spread": round(probability_spread, 4),
            "data_coverage": round(coverage, 3),
        }

    @staticmethod
    def _explanations(features: dict, home_team: str, away_team: str) -> list[str]:
        """Create plain-language explanations from the same pre-match inputs used by the model."""
        factors = ["Home advantage is included for " + home_team + "."]

        home_form, away_form = features["home_form_points_5"], features["away_form_points_5"]
        if abs(home_form - away_form) >= 0.25:
            leader = home_team if home_form > away_form else away_team
            factors.append(f"{leader} has the stronger recent five-match form.")

        home_attack, away_attack = features["home_attack_strength"], features["away_attack_strength"]
        if abs(home_attack - away_attack) >= 0.15:
            leader = home_team if home_attack > away_attack else away_team
            factors.append(f"{leader} has the stronger recorded attack rate.")

        home_defence, away_defence = features["home_defence_strength"], features["away_defence_strength"]
        if abs(home_defence - away_defence) >= 0.15:
            leader = home_team if home_defence < away_defence else away_team
            factors.append(f"{leader} has the stronger recorded defensive rate.")

        rest_difference = features["rest_days_difference"]
        if abs(rest_difference) >= 2:
            rested_team = home_team if rest_difference > 0 else away_team
            factors.append(f"{rested_team} has had more rest before this fixture.")

        if features["h2h_matches"] >= 2 and abs(features["home_h2h_points_per_game"] - 1.0) >= 0.35:
            leader = home_team if features["home_h2h_points_per_game"] > 1.0 else away_team
            factors.append(f"Previous head-to-head results favour {leader}.")

        return factors[:4]

    @staticmethod
    def _score_prediction(home_expected_goals: float, away_expected_goals: float) -> dict:
        """Convert expected goals into the most likely exact scorelines."""
        home_expected_goals = max(0.15, min(float(home_expected_goals), 4.5))
        away_expected_goals = max(0.15, min(float(away_expected_goals), 4.5))
        scorelines = []
        for home_goals in range(6):
            home_probability = exp(-home_expected_goals) * home_expected_goals ** home_goals / factorial(home_goals)
            for away_goals in range(6):
                away_probability = exp(-away_expected_goals) * away_expected_goals ** away_goals / factorial(away_goals)
                scorelines.append({
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "score": f"{home_goals}–{away_goals}",
                    "probability": round(home_probability * away_probability, 4),
                })
        likely_scorelines = sorted(scorelines, key=lambda scoreline: scoreline["probability"], reverse=True)[:3]
        return {
            "home_expected_goals": round(home_expected_goals, 2),
            "away_expected_goals": round(away_expected_goals, 2),
            "most_likely_score": likely_scorelines[0],
            "likely_scorelines": likely_scorelines,
        }

    @staticmethod
    def _poisson_outcome_probabilities(home_expected_goals: float, away_expected_goals: float) -> dict[int, float]:
        """Outcome probabilities implied by the separate expected-goal models."""
        home = max(0.15, min(float(home_expected_goals), 4.5))
        away = max(0.15, min(float(away_expected_goals), 4.5))
        totals = {0: 0.0, 1: 0.0, 2: 0.0}
        # Eight goals captures virtually all mass in the normal fixture range.
        for home_goals in range(9):
            for away_goals in range(9):
                probability = exp(-home) * home ** home_goals / factorial(home_goals)
                probability *= exp(-away) * away ** away_goals / factorial(away_goals)
                totals[2 if home_goals > away_goals else 1 if home_goals == away_goals else 0] += probability
        normaliser = sum(totals.values()) or 1.0
        return {key: value / normaliser for key, value in totals.items()}

    @staticmethod
    def _elo_outcome_probabilities(features: dict) -> dict[int, float]:
        """A transparent ELO signal, kept independent of the ML probability."""
        home_rating = float(features["home_elo"]) + 70.0
        away_rating = float(features["away_elo"])
        home_non_draw = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
        closeness = max(0.0, 1 - abs(home_rating - away_rating) / 500)
        draw = 0.19 + 0.10 * closeness
        return {2: (1 - draw) * home_non_draw, 1: draw, 0: (1 - draw) * (1 - home_non_draw)}

    @staticmethod
    def _ensemble_probabilities(ml: dict[int, float], elo: dict[int, float], poisson_signal: dict[int, float]) -> dict[int, float]:
        # We intentionally expose the components below; the ensemble is an
        # evidence-weighted forecast, not a black-box certainty claim.
        values = {key: 0.50 * ml.get(key, 0) + 0.25 * elo.get(key, 0) + 0.25 * poisson_signal.get(key, 0) for key in (0, 1, 2)}
        total = sum(values.values()) or 1.0
        return {key: value / total for key, value in values.items()}

    def _similar_matches(self, league: str, features: dict, match_date: datetime | None, limit: int = 5) -> list[dict]:
        """Find past same-league fixtures closest on pre-match ELO, form and strength."""
        if not self.historical_examples:
            return []
        candidates = []
        fields = ("elo_difference", "home_form_points_5", "away_form_points_5", "home_attack_strength", "away_attack_strength", "home_defence_strength", "away_defence_strength")
        scales = {"elo_difference": 180, "home_form_points_5": 1.5, "away_form_points_5": 1.5,
                  "home_attack_strength": 1.5, "away_attack_strength": 1.5,
                  "home_defence_strength": 1.5, "away_defence_strength": 1.5}
        for example in self.historical_examples:
            if example.get("league") != league:
                continue
            example_date = pd.to_datetime(example.get("match_date"), errors="coerce")
            if match_date and not pd.isna(example_date) and example_date.to_pydatetime() >= match_date:
                continue
            prior = example.get("features", {})
            distance = sum(abs(float(features[field]) - float(prior.get(field, 0))) / scales[field] for field in fields)
            candidates.append((distance, example))
        candidates.sort(key=lambda item: item[0])
        closest = candidates[:limit]
        return [{
            "date": item["match_date"], "home_team": item["home_team"], "away_team": item["away_team"],
            "score": f'{item["home_goals"]}–{item["away_goals"]}',
            "outcome": {0: "Away Win", 1: "Draw", 2: "Home Win"}[item["result"]],
            "similarity": round(max(0.0, 1 - distance / 8), 3),
        } for distance, item in closest]

    def predict_fixtures(self, fixtures: list[dict], *, reference_time: datetime | None = None) -> list[dict]:
        """Predict a fixture batch with one efficient model call."""
        if self.pipeline is None:
            raise RuntimeError("Train or load the model before predicting.")
        if self.home_goals_pipeline is None or self.away_goals_pipeline is None:
            raise RuntimeError("Expected-goals models have not been trained.")
        feature_rows, resolved_fixtures = [], []
        for fixture in fixtures:
            league, home_team, away_team = fixture["league"], fixture["home_team"], fixture["away_team"]
            home, home_match = self._resolve_team(league, home_team)
            away, away_match = self._resolve_team(league, away_team)
            if min(home_match, away_match) < 1.0:
                raise ValueError("Verified team history is unavailable for one or both clubs in this competition.")
            if home == away:
                raise ValueError("A fixture must contain two distinct clubs.")
            if self.feature_schema_version != FEATURE_SCHEMA_VERSION:
                raise ValueError("Prediction model needs retraining with the current season-aware features.")
            if self.leakage_protocol_version != PROTOCOL_VERSION or not self.training_data_through:
                raise ValueError('Model training cutoff is unverified. Retrain before generating predictions.')
            fixture_date = pd.to_datetime(fixture.get("utc_date"), errors="coerce")
            if not pd.isna(fixture_date) and fixture_date.tzinfo is not None:
                fixture_date = fixture_date.tz_convert("UTC").tz_localize(None)
            if pd.isna(fixture_date) or pd.Timestamp(self.training_data_through).date() >= fixture_date.date():
                raise ValueError('Training results must strictly precede the fixture day. Use a walk-forward model for historical matches.')
            last_result = max((state.last_match_date for key, state in self.states.items()
                               if key.startswith(f"{league}:") and state.last_match_date), default=None)
            if last_result and not pd.isna(fixture_date) and fixture_date.date() <= last_result.date():
                raise ValueError("Historical fixtures require a point-in-time backtest, not the current model states.")
            reference_day = (reference_time or datetime.now(timezone.utc)).date()
            if (pd.Timestamp(self.training_data_through).date() >= reference_day
                    or (last_result and last_result.date() >= reference_day)):
                raise ValueError('Training and form results must precede the prediction reference day.')
            if not last_result or ((reference_time or datetime.now(timezone.utc)).date() - last_result.date()).days > 45:
                raise ValueError("Recent verified results are unavailable for this competition; forecasts are paused until history refreshes.")
            members = self.league_members.get(league, set())
            if self._state_key(league, home) not in members or self._state_key(league, away) not in members:
                raise ValueError("One or both clubs lack verified current-season membership in this competition.")
            feature_rows.append(self._features(
                league, home, away,
                fixture_date.to_pydatetime() if not pd.isna(fixture_date) else None,
            ))
            resolved_fixtures.append((fixture, home, away, home_match, away_match, feature_rows[-1], last_result))
        features = pd.DataFrame(feature_rows, columns=FEATURE_COLUMNS)
        probabilities = self.pipeline.predict_proba(features)
        outcomes = self.pipeline.predict(features)
        home_goal_predictions = self.home_goals_pipeline.predict(features)
        away_goal_predictions = self.away_goals_pipeline.predict(features)
        results = []
        for (fixture, home, away, home_match, away_match, features, last_result), probability, outcome, home_xg, away_xg in zip(
            resolved_fixtures, probabilities, outcomes, home_goal_predictions, away_goal_predictions,
        ):
            probability_by_class = dict(zip(self.pipeline.classes_, probability))
            score_prediction = self._score_prediction(home_xg, away_xg)
            elo_probabilities = self._elo_outcome_probabilities(features)
            poisson_probabilities = self._poisson_outcome_probabilities(home_xg, away_xg)
            ensemble_probabilities = self._ensemble_probabilities(probability_by_class, elo_probabilities, poisson_probabilities)
            outcome_code = max(ensemble_probabilities, key=ensemble_probabilities.get)
            coverage = min(home_match, away_match)
            signal_outcomes = [
                max(probability_by_class, key=probability_by_class.get),
                max(elo_probabilities, key=elo_probabilities.get),
                max(poisson_probabilities, key=poisson_probabilities.get),
            ]
            agreement = len(set(signal_outcomes)) == 1
            results.append({
                **fixture,
                "feature_schema_version": self.feature_schema_version,
                "model_version": self.model_version,
                "leakage_protocol_version": self.leakage_protocol_version,
                "training_data_through": self.training_data_through,
                "history_through": str(last_result.date()),
                "home_win_probability": round(float(ensemble_probabilities.get(2, 0)), 4),
                "draw_probability": round(float(ensemble_probabilities.get(1, 0)), 4),
                "away_win_probability": round(float(ensemble_probabilities.get(0, 0)), 4),
                "predicted_outcome": {0: "Away Win", 1: "Draw", 2: "Home Win"}[int(outcome_code)],
                "home_name_match": round(home_match, 3), "away_name_match": round(away_match, 3),
                "name_mapping_confidence": round(coverage, 3),
                "prediction_status": "ready" if coverage >= 0.8 else "review_required",
                "confidence": self._confidence(ensemble_probabilities, coverage),
                "form_insights": {
                    "home": self._form_summary(self.states[self._state_key(fixture["league"], home)]),
                    "away": self._form_summary(self.states[self._state_key(fixture["league"], away)]),
                },
                "team_comparison": {
                    "home": {
                        "attack": round(features["home_attack_strength"], 2),
                        "defence": round(features["home_defence_strength"], 2),
                        "form_points": round(features["home_form_points_5"], 2),
                        "rest_days": int(features["home_rest_days"]),
                    },
                    "away": {
                        "attack": round(features["away_attack_strength"], 2),
                        "defence": round(features["away_defence_strength"], 2),
                        "form_points": round(features["away_form_points_5"], 2),
                        "rest_days": int(features["away_rest_days"]),
                    },
                    "head_to_head_matches": int(features["h2h_matches"]),
                },
                "explanations": self._explanations(features, fixture["home_team"], fixture["away_team"]),
                "score_prediction": score_prediction,
                "ensemble": {
                    "name": "Outcome ML + ELO + goal model",
                    "agreement": "Models agree" if agreement else "Models show mixed signals",
                    "signals": {
                        "outcome_ml": {"home": round(float(probability_by_class.get(2, 0)), 4), "draw": round(float(probability_by_class.get(1, 0)), 4), "away": round(float(probability_by_class.get(0, 0)), 4)},
                        "elo_strength": {"home": round(elo_probabilities[2], 4), "draw": round(elo_probabilities[1], 4), "away": round(elo_probabilities[0], 4)},
                        "goal_model": {"home": round(poisson_probabilities[2], 4), "draw": round(poisson_probabilities[1], 4), "away": round(poisson_probabilities[0], 4)},
                    },
                },
                "similar_matches": self._similar_matches(fixture["league"], features, fixture.get("utc_date")),
                "data_coverage": {
                    "historical_team_mapping": round(coverage, 3),
                    "player_availability": "not_connected",
                    "venue_and_referee": "not_connected",
                    "basis": "Historical results, ELO, league form, home/away strength, rest and head-to-head.",
                },
            })
        return results


def save_predictions_for_scheduled_matches(match_date: str | None = "2026-08-08") -> Path:
    """Train on CSV history and save predictions for database fixtures on a date."""
    from app.db.session import SessionLocal
    from app.models.competition import Competition
    from app.models.match import Match
    from app.models.team import Team

    artifact_path = MODELS_DIR / "historical_match_model.joblib"
    model = HistoricalMatchModel.load(artifact_path) if artifact_path.exists() else HistoricalMatchModel()
    metrics = joblib.load(artifact_path)["metrics"] if artifact_path.exists() else model.train()
    db = SessionLocal()
    try:
        query = (
            db.query(Match, Competition.code, Team.name)
            .join(Competition, Match.competition_id == Competition.id)
            .join(Team, Match.home_team_id == Team.id)
            .filter(Match.status == "SCHEDULED")
        )
        if match_date:
            query = query.filter(Match.match_date == datetime.fromisoformat(match_date).date())
        matches = query.order_by(Match.utc_date.asc()).all()
        fixtures = []
        for match, league, home_team in matches:
            away_team = db.get(Team, match.away_team_id).name
            fixtures.append({
                "match_id": match.id, "utc_date": match.utc_date, "league": league,
                "home_team": home_team, "away_team": away_team,
            })
        results = model.predict_fixtures(fixtures)
    finally:
        db.close()
    output = REPORTS_DIR / f"historical_predictions_{match_date or 'all_scheduled'}.csv"
    pd.DataFrame(results).to_csv(output, index=False)
    print(f"Model metrics: {metrics}")
    print(f"Saved {len(results)} predictions to {output}")
    return output


if __name__ == "__main__":
    print(save_predictions_for_scheduled_matches())
