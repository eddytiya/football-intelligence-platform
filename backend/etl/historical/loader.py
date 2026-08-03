from typing import Dict

from loguru import logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

from app.models.competition import Competition
from app.models.season import Season
from app.models.team import Team
from app.models.match import Match
from app.models.team_statistics import TeamStatistics
from app.models.betting_odds import BettingOdds
from etl.historical.extractor import HistoricalExtractor
from etl.historical.transformer import HistoricalTransformer

class HistoricalLoader:
    """
    Loads transformed historical football data into PostgreSQL.

    Responsibilities
    ----------------
    - Load competitions
    - Load seasons
    - Load teams
    - Load matches
    - Load team statistics
    - Load betting odds
    - Prevent duplicates
    - Commit transactions
    """

    def __init__(self):

        logger.info(
            "Historical Loader initialized."
        )

        self.db: Session = SessionLocal()

        # Cache database IDs
        self.competition_ids = {}
        self.season_ids = {}
        self.team_ids = {}
        self.match_ids = {}

    # ==========================================================
    # Helpers
    # ==========================================================

    def commit(self):
        """
        Commit current transaction.
        """

        self.db.commit()

    def rollback(self):
        """
        Rollback current transaction.
        """

        self.db.rollback()

    def close(self):
        """
        Close database session.
        """

        self.db.close()

    # ==========================================================
    # Cache Builders
    # ==========================================================

    def refresh_competition_cache(self):
        """
        Cache all competitions.
        """

        self.competition_ids = {
            competition.code: competition.id
            for competition in self.db.query(
                Competition
            ).all()
        }

    def refresh_season_cache(self):
        """
        Cache all seasons.
        """

        self.season_ids = {
            (
                season.competition_id,
                season.start_year,
            ): season.id
            for season in self.db.query(
                Season
            ).all()
        }

    def refresh_team_cache(self):
        """
        Cache all teams.
        """

        self.team_ids = {
            team.name: team.id
            for team in self.db.query(
                Team
            ).all()
        }

    def refresh_match_cache(self):
        """
        Cache all matches.
        """

        self.match_ids = {
            match.api_id: match.id
            for match in self.db.query(
                Match
            ).all()
        }

    def refresh_all_caches(self):
        """
        Refresh every cache.
        """

        self.refresh_competition_cache()

        self.refresh_season_cache()

        self.refresh_team_cache()

        self.refresh_match_cache()

        # ==========================================================
    # Competition Loader
    # ==========================================================

    def load_competitions(
        self,
        competitions,
    ):
        """
        Load competitions into database.
        """

        logger.info(
            "Loading competitions..."
        )

        inserted = 0

        for competition in competitions:

            exists = self.db.query(
                Competition
            ).filter_by(
                code=competition["code"]
            ).first()

            if exists:
                continue

            self.db.add(
                Competition(
                    code=competition["code"],
                    name=competition["name"],
                )
            )

            inserted += 1

        self.commit()

        self.refresh_competition_cache()

        logger.success(
            f"Competitions loaded: {inserted}"
        )

    # ==========================================================
    # Season Loader
    # ==========================================================

    def load_seasons(
        self,
        seasons,
    ):
        """
        Load seasons into database.
        """

        logger.info(
            "Loading seasons..."
        )

        inserted = 0

        for season in seasons:

            competition_id = self.competition_ids.get(
                season["competition_code"]
            )

            if competition_id is None:
                continue

            exists = (
                self.db.query(Season)
                .filter_by(
                    competition_id=competition_id,
                    start_year=season["start_year"],
                )
                .first()
            )

            if exists:
                continue

            self.db.add(
                Season(
                    api_id=season["api_id"],
                    competition_id=competition_id,
                    season_name=season["season_name"],
                    start_year=season["start_year"],
                    end_year=season["end_year"],
                    start_date=season["start_date"],
                    end_date=season["end_date"],
                    current_matchday=season["current_matchday"],
                )
            )

            inserted += 1

        self.commit()

        self.refresh_season_cache()

        logger.success(
            f"Seasons loaded: {inserted}"
        )

    # ==========================================================
    # Team Loader
    # ==========================================================

    def load_teams(
        self,
        teams,
    ):
        """
        Load teams into database.
        """

        logger.info(
            "Loading teams..."
        )

        inserted = 0

        for team in teams:

            exists = self.db.query(
                Team
            ).filter_by(
                name=team["name"]
            ).first()

            if exists:
                continue

            self.db.add(
                Team(
                    name=team["name"],
                )
            )

            inserted += 1

        self.commit()

        self.refresh_team_cache()

        logger.success(
            f"Teams loaded: {inserted}"
        )
        # ==========================================================
    # Match Loader
    # ==========================================================

    def load_matches(
        self,
        matches,
    ):
        """
        Load historical matches into database.
        """

        logger.info(
            "Loading matches..."
        )

        inserted = 0

        for match in matches:

            # Skip if already exists
            exists = (
                self.db.query(Match)
                .filter_by(
                    api_id=match["api_id"]
                )
                .first()
            )

            if exists:
                continue

            competition_id = self.competition_ids.get(
                match["competition_code"]
            )

            if competition_id is None:
                continue

            season_id = self.season_ids.get(
                (
                    competition_id,
                    int(match["season"]),
                )
            )

            if season_id is None:
                continue

            home_team_id = self.team_ids.get(
                match["home_team"]
            )

            away_team_id = self.team_ids.get(
                match["away_team"]
            )

            if (
                home_team_id is None
                or away_team_id is None
            ):
                continue

            self.db.add(
                Match(
                    api_id=match["api_id"],
                    competition_id=competition_id,
                    season_id=season_id,

                    referee_id=None,
                    stadium_id=None,

                    home_team_id=home_team_id,
                    away_team_id=away_team_id,

                    utc_date=None,
                    match_date=match["match_date"],
                    kick_off=None,

                    status=match["status"],
                    stage=match["stage"],
                    match_week=match["match_week"],

                    home_score=match["home_score"],
                    away_score=match["away_score"],
                )
            )

            inserted += 1

        self.commit()

        self.refresh_match_cache()

        logger.success(
            f"Matches loaded: {inserted}"
        )
        # ==========================================================
    # Team Statistics Loader
    # ==========================================================

    def load_team_statistics(
        self,
        statistics,
    ):
        """
        Load team statistics into database.
        """

        logger.info(
            "Loading team statistics..."
        )

        inserted = 0

        for stat in statistics:

            match_id = self.match_ids.get(
                stat["match_api_id"]
            )

            if match_id is None:
                continue

            team_id = self.team_ids.get(
                stat["team_name"]
            )

            if team_id is None:
                continue

            exists = (
                self.db.query(TeamStatistics)
                .filter_by(
                    match_id=match_id,
                    team_id=team_id,
                )
                .first()
            )

            if exists:
                continue

            self.db.add(
                TeamStatistics(
                    match_id=match_id,
                    team_id=team_id,

                    possession=None,

                    shots=stat["shots"],
                    shots_on_target=stat["shots_on_target"],
                    shots_off_target=None,
                    blocked_shots=None,
                    shots_inside_box=None,
                    shots_outside_box=None,

                    expected_goals=None,

                    passes=None,
                    accurate_passes=None,
                    pass_accuracy=None,

                    corners=stat["corners"],
                    offsides=None,

                    big_chances=None,
                    big_chances_missed=None,

                    tackles=None,
                    interceptions=None,
                    clearances=None,
                    saves=None,
                    blocked_passes=None,

                    fouls=stat["fouls"],

                    yellow_cards=stat["yellow_cards"],
                    red_cards=stat["red_cards"],

                    aerial_duels_won=None,
                    aerial_duels_lost=None,

                    dribbles=None,
                    successful_dribbles=None,

                    clean_sheet=None,
                    penalties_saved=None,
                )
            )

            inserted += 1

        self.commit()

        logger.success(
            f"Team statistics loaded: {inserted}"
        )

    # ==========================================================
    # Betting Odds Loader
    # ==========================================================

    def load_betting_odds(
        self,
        odds_list,
    ):
        """
        Load betting odds into database.
        """

        logger.info(
            "Loading betting odds..."
        )

        inserted = 0

        for odds in odds_list:

            match_id = self.match_ids.get(
                odds["match_api_id"]
            )

            if match_id is None:
                continue

            exists = self.db.query(
                BettingOdds
            ).filter_by(
                match_id=match_id,
                bookmaker=odds["bookmaker"],
            ).first()

            if exists:
                continue

            self.db.add(
                BettingOdds(

                    match_id=match_id,

                    bookmaker=odds["bookmaker"],

                    home_win=odds["home_win"],

                    draw=odds["draw"],

                    away_win=odds["away_win"],

                    over_2_5=odds["over_2_5"],

                    under_2_5=odds["under_2_5"],

                    btts_yes=odds["btts_yes"],

                    btts_no=odds["btts_no"],

                    handicap=odds["handicap"],

                    handicap_home=odds["handicap_home"],

                    handicap_away=odds["handicap_away"],

                    home_draw=odds["home_draw"],

                    home_away=odds["home_away"],

                    draw_away=odds["draw_away"],
                )
            )

            inserted += 1

        self.commit()

        logger.success(
            f"Betting odds loaded: {inserted}"
        )
        # ==========================================================
    # Main Loader
    # ==========================================================

    def load_all(
        self,
        transformed: Dict,
    ):
        """
        Load all transformed historical data into database.
        """

        logger.info(
            "Starting historical database loading..."
        )

        try:

            # Load in dependency order

            self.load_competitions(
                transformed["competitions"]
            )

            self.load_seasons(
                transformed["seasons"]
            )

            self.load_teams(
                transformed["teams"]
            )

            self.load_matches(
                transformed["matches"]
            )

            self.load_team_statistics(
                transformed["team_statistics"]
            )

            self.load_betting_odds(
                transformed["betting_odds"]
            )

            logger.success(
                "Historical data loaded successfully."
            )

        except Exception as e:

            self.rollback()

            logger.exception(e)

            raise

        finally:

            self.close()

def main():

    logger.info(
        "=" * 70
    )

    logger.info(
        "Historical ETL Loader"
    )

    logger.info(
        "=" * 70
    )

    # ------------------------------------------
    # Extract
    # ------------------------------------------

    extractor = HistoricalExtractor()

    datasets = extractor.extract_all()

    # ------------------------------------------
    # Transform
    # ------------------------------------------

    transformer = HistoricalTransformer()

    transformed = transformer.transform_all(
        datasets
    )

    # ------------------------------------------
    # Load
    # ------------------------------------------

    loader = HistoricalLoader()

    loader.load_all(
        transformed
    )

    print()

    print("=" * 70)

    print("Historical ETL Completed")

    print("=" * 70)

    print(
        f"Competitions    : {len(transformed['competitions'])}"
    )

    print(
        f"Seasons         : {len(transformed['seasons'])}"
    )

    print(
        f"Teams           : {len(transformed['teams'])}"
    )

    print(
        f"Matches         : {len(transformed['matches'])}"
    )

    print(
        f"Team Statistics : {len(transformed['team_statistics'])}"
    )

    print(
        f"Betting Odds    : {len(transformed['betting_odds'])}"
    )


if __name__ == "__main__":
    main()