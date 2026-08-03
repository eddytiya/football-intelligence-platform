from datetime import datetime

from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.match import Match
from app.models.season import Season
from app.models.team import Team
from app.repositories.competition_repository import CompetitionRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.season_repository import SeasonRepository
from app.repositories.team_repository import TeamRepository


class FootballDataService:
    """
    Central service responsible for retrieving football data.

    All application modules should retrieve football
    data through this service instead of directly
    querying repositories.
    """

    def __init__(self, db: Session):
        self.db = db

        self.team_repository = TeamRepository(db)
        self.competition_repository = CompetitionRepository(db)
        self.season_repository = SeasonRepository(db)
        self.match_repository = MatchRepository(db)

    # ==========================================================
    # Teams
    # ==========================================================

    def get_team(
        self,
        team_id: int,
    ) -> Team | None:
        """
        Return a team by database ID.
        """

        return self.team_repository.get_team_by_id(team_id)

    def get_team_by_api_id(
        self,
        api_id: int,
    ) -> Team | None:
        """
        Return a team by Football-Data API ID.
        """

        return self.team_repository.get_team_by_api_id(api_id)

    def get_team_by_name(
        self,
        name: str,
    ) -> Team | None:
        """
        Return a team by name.
        """

        return self.team_repository.get_team_by_name(name)

    def get_all_teams(
        self,
    ) -> list[Team]:
        """
        Return all teams.
        """

        return self.team_repository.get_all_teams()

    # ==========================================================
    # Competitions
    # ==========================================================

    def get_all_competitions(
        self,
    ) -> list[Competition]:
        """
        Return all competitions.
        """

        return self.competition_repository.get_all_competitions()

    # ==========================================================
    # Seasons
    # ==========================================================

    def get_season(
        self,
        season_id: int,
    ) -> Season | None:
        """
        Return season by database ID.
        """

        return self.season_repository.get_season_by_id(season_id)

    def get_season_by_api_id(
        self,
        api_id: int,
    ) -> Season | None:
        """
        Return season by API ID.
        """

        return self.season_repository.get_season_by_api_id(api_id)

    def get_all_seasons(
        self,
    ) -> list[Season]:
        """
        Return all seasons.
        """

        return self.season_repository.get_all_seasons()

    # ==========================================================
    # Matches
    # ==========================================================

    def get_match(
        self,
        match_id: int,
    ) -> Match | None:
        """
        Return a match by ID.
        """

        return self.match_repository.get_match_by_id(match_id)

    def get_finished_matches(
        self,
    ) -> list[Match]:
        """
        Return all finished matches.
        """

        return self.match_repository.get_finished_matches()

    def get_upcoming_matches(
        self,
        limit: int | None = None,
    ) -> list[Match]:
        """
        Return upcoming matches.
        """

        return self.match_repository.get_upcoming_matches(limit)

    def get_today_matches(
        self,
        today: datetime,
    ) -> list[Match]:
        """
        Return today's scheduled matches.
        """

        return self.match_repository.get_today_matches(today)

    def get_matches_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Match]:
        """
        Return matches between two dates.
        """

        return self.match_repository.get_matches_between_dates(
            start_date,
            end_date,
        )

    def get_next_match(
        self,
    ) -> Match | None:
        """
        Return the next scheduled match.
        """

        return self.match_repository.get_next_match()