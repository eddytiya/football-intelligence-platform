from datetime import datetime
from typing import Dict, List

import pandas as pd
from loguru import logger
from etl.historical.extractor import HistoricalExtractor


class HistoricalTransformer:
    """
    Transforms historical football-data.co.uk datasets
    into structured objects ready for database loading.

    Responsibilities
    ----------------
    - Clean raw datasets
    - Validate required columns
    - Normalize data
    - Build competitions
    - Build seasons
    - Build teams
    - Build matches
    - Build team statistics
    - Build betting odds
    """

    # ==========================================================
    # Competition Mapping
    # ==========================================================

    LEAGUE_MAPPING = {
        "PL": {
            "code": "PL",
            "name": "Premier League",
        },
        "PD": {
            "code": "PD",
            "name": "La Liga",
        },
        "SA": {
            "code": "SA",
            "name": "Serie A",
        },
        "BL1": {
            "code": "BL1",
            "name": "Bundesliga",
        },
        "FL1": {
            "code": "FL1",
            "name": "Ligue 1",
        },
        "DED": {
            "code": "DED",
            "name": "Eredivisie",
        },
        "PPL": {
            "code": "PPL",
            "name": "Primeira Liga",
        },
        "ELC": {
            "code": "ELC",
            "name": "Championship",
        },
    }

    # ==========================================================
    # Constructor
    # ==========================================================

    def __init__(self):

        logger.info(
            "Historical Transformer initialized."
        )

        # Prevent duplicate objects

        self.competitions = {}

        self.seasons = {}

        self.teams = {}

        self.matches = []

        self.team_statistics = []
        self.betting_odds = []

    # ==========================================================
    # Validation
    # ==========================================================

    REQUIRED_COLUMNS = [
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    ]

    def validate_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
    ) -> bool:
        """
        Validate a dataset before transformation.
        """

        missing = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing:

            logger.warning(
                f"{dataset_name} missing columns: {missing}"
            )

            return False

        return True

    # ==========================================================
    # Helpers
    # ==========================================================

    @staticmethod
    def parse_date(value):

        if pd.isna(value):

            return None

        try:

            return datetime.strptime(
                str(value),
                "%d/%m/%Y",
            ).date()

        except Exception:

            return None

    @staticmethod
    def parse_score(value):

        if pd.isna(value):

            return 0

        try:

            return int(value)

        except Exception:

            return 0

    # --------------------------------------------------------------------------------------------------

    @staticmethod
    def get_int(
        row: pd.Series,
        column: str,
    ):
        """
        Safely return an integer value from a CSV column.
        """

        if column not in row.index:
            return None

        value = row[column]

        if pd.isna(value):
            return None

        try:
            return int(value)
        except Exception:
            return None


    @staticmethod
    def get_float(
        row: pd.Series,
        column: str,
    ):
        """
        Safely return a float value from a CSV column.
        """

        if column not in row.index:
            return None

        value = row[column]

        if pd.isna(value):
            return None

        try:
            return float(value)
        except Exception:
            return None
    def transform_competition(
        self,
        league_code: str,
    ):
        """
        Build a unique competition.
        """

        if league_code in self.competitions:
            return

        competition = self.LEAGUE_MAPPING.get(
            league_code
        )

        if competition is None:

            logger.warning(
                f"Unknown league: {league_code}"
            )

            return

        self.competitions[league_code] = {
            "code": competition["code"],
            "name": competition["name"],
        }




    def transform_season(
        self,
        competition_code: str,
        season: int,
    ):
        """
        Transform season information.
        """

        season_name = f"{season}/{str(season + 1)[-2:]}"

        season_data = {
            "api_id": None,
            "competition_code": competition_code,
            "season_name": season_name,
            "start_year": season,
            "end_year": season + 1,
            "start_date": None,
            "end_date": None,
            "current_matchday": None,
        }

        key = (
            competition_code,
            season,
        )

        if key not in self.seasons:
            self.seasons[key] = season_data

    def transform_team(
        self,
        team_name: str,
    ):
        """
        Build a unique team.
        """

        if pd.isna(team_name):
            return

        team_name = str(team_name).strip()

        if team_name == "":
            return

        if team_name in self.teams:
            return

        self.teams[team_name] = {
            "name": team_name,
        }

    def transform_teams(
        self,
        df: pd.DataFrame,
    ):
        """
        Extract every team in a dataset.
        """

        for _, row in df.iterrows():

            self.transform_team(
                row["HomeTeam"]
            )

            self.transform_team(
                row["AwayTeam"]
            )

    def build_match_id(
        self,
        league_code: str,
        season: str,
        row: pd.Series,
    ):
        """
        Build a unique historical match ID.
        """

        return (
            f"{league_code}_"
            f"{season}_"
            f"{row['HomeTeam']}_"
            f"{row['AwayTeam']}_"
            f"{row['Date']}"
        )

    def transform_matches(
        self,
        df: pd.DataFrame,
        league_code: str,
        season: str,
    ):
        """
        Transform every row into a match dictionary.
        """

        for _, row in df.iterrows():

            match = {

                "api_id": self.build_match_id(
                    league_code,
                    season,
                    row,
                ),

                "competition_code": league_code,

                "season": season,

                "match_date": self.parse_date(
                    row["Date"]
                ),

                "home_team": row["HomeTeam"],

                "away_team": row["AwayTeam"],

                "home_score": self.parse_score(
                    row["FTHG"]
                ),

                "away_score": self.parse_score(
                    row["FTAG"]
                ),

                "status": "FINISHED",

                "stage": "REGULAR_SEASON",

                "match_week": None,
            }

            self.matches.append(match)


    def transform_team_statistics(
        self,
        df: pd.DataFrame,
        league_code: str,
        season: str,
    ):
        """
        Create home and away team statistics for every match.
        """

        for _, row in df.iterrows():

            match_id = self.build_match_id(
                league_code,
                season,
                row,
            )

            # -------------------------
            # Home Team
            # -------------------------

            home_stats = {

                "match_api_id": match_id,

                "team_name": row["HomeTeam"],

                "is_home": True,

                "goals": self.parse_score(
                    row["FTHG"]
                ),

                "shots": self.get_int(
                    row,
                    "HS",
                ),

                "shots_on_target": self.get_int(
                    row,
                    "HST",
                ),

                "corners": self.get_int(
                    row,
                    "HC",
                ),

                "fouls": self.get_int(
                    row,
                    "HF",
                ),

                "yellow_cards": self.get_int(
                    row,
                    "HY",
                ),

                "red_cards": self.get_int(
                    row,
                    "HR",
                ),
            }

            # -------------------------
            # Away Team
            # -------------------------

            away_stats = {

                "match_api_id": match_id,

                "team_name": row["AwayTeam"],

                "is_home": False,

                "goals": self.parse_score(
                    row["FTAG"]
                ),

                "shots": self.get_int(
                    row,
                    "AS",
                ),

                "shots_on_target": self.get_int(
                    row,
                    "AST",
                ),

                "corners": self.get_int(
                    row,
                    "AC",
                ),

                "fouls": self.get_int(
                    row,
                    "AF",
                ),

                "yellow_cards": self.get_int(
                    row,
                    "AY",
                ),

                "red_cards": self.get_int(
                    row,
                    "AR",
                ),
            }

            self.team_statistics.append(home_stats)
            self.team_statistics.append(away_stats)

    def transform_betting_odds(
        self,
        df: pd.DataFrame,
        league_code: str,
        season: str,
    ):
        """
        Transform betting odds for every match.
        """

        for _, row in df.iterrows():

            match_id = self.build_match_id(
                league_code,
                season,
                row,
            )

            odds = {

                "match_api_id": match_id,

                "bookmaker": "Bet365",

                # Match Result
                "home_win": self.get_float(row, "B365H"),
                "draw": self.get_float(row, "B365D"),
                "away_win": self.get_float(row, "B365A"),

                # Over / Under
                "over_2_5": (
                    self.get_float(row, "B365>2.5")
                    or self.get_float(row, "B365O2.5")
                ),

                "under_2_5": (
                    self.get_float(row, "B365<2.5")
                    or self.get_float(row, "B365U2.5")
                ),

                # Both Teams To Score
                "btts_yes": (
                    self.get_float(row, "B365BTTS")
                    or self.get_float(row, "B365BTS")
                ),

                "btts_no": None,

                # Asian Handicap
                "handicap": self.get_float(row, "AHh"),
                "handicap_home": self.get_float(row, "B365AHH"),
                "handicap_away": self.get_float(row, "B365AHA"),

                # Double Chance
                "home_draw": self.get_float(row, "B365HD"),
                "home_away": self.get_float(row, "B365HA"),
                "draw_away": self.get_float(row, "B365DA"),
            }

            self.betting_odds.append(odds)
    # ==========================================================
    # Main Transformation
    # ==========================================================

    def transform_all(
        self,
        datasets: Dict[str, pd.DataFrame],
    ):
        """
        Transform every historical dataset.
        """

        logger.info(
            "Starting historical transformation..."
        )

        transformed = {
            "competitions": [],
            "seasons": [],
            "teams": [],
            "matches": [],
            "team_statistics": [],
            "betting_odds": [],
        }

        for dataset_name, df in datasets.items():

            logger.info(
                f"Processing {dataset_name}"
            )

            if not self.validate_dataset(
                df,
                dataset_name,
            ):
                continue

            league_code, season = dataset_name.split("_")
            season = int(season)

            self.transform_competition(
                league_code
            )

            self.transform_season(
                league_code,
                season,
            )

            self.transform_teams(
                df,
            )

            self.transform_matches(
                df,
                league_code,
                season,
            )
            self.transform_team_statistics(
                df,
                league_code,
                season,
            )
            self.transform_betting_odds(
                df,
                league_code,
                season,
            )

        logger.success(
            "Historical transformation completed."
        )

        transformed["competitions"] = list(
            self.competitions.values()
        )

        transformed["seasons"] = list(
            self.seasons.values()
        )

        transformed["teams"] = list(
            self.teams.values()
        )

        transformed["matches"] = self.matches

        transformed["team_statistics"] = (
            self.team_statistics
        )

        transformed["betting_odds"] = (
            self.betting_odds
        )

        return transformed


def main():

    extractor = HistoricalExtractor()

    datasets = extractor.extract_all()

    transformer = HistoricalTransformer()

    transformed = transformer.transform_all(datasets)

    print("\n")
    print("=" * 70)
    print("Historical Transformation Summary")
    print("=" * 70)

    print(f"Competitions    : {len(transformed['competitions'])}")
    print(f"Seasons         : {len(transformed['seasons'])}")
    print(f"Teams           : {len(transformed['teams'])}")
    print(f"Matches         : {len(transformed['matches'])}")
    print(f"Team Statistics : {len(transformed['team_statistics'])}")
    print(f"Betting Odds    : {len(transformed['betting_odds'])}")


if __name__ == "__main__":
    main()