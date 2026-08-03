from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.match_repository import MatchRepository
from app.schemas.match import (
    MatchDetailResponse,
    UpcomingMatchResponse,
)


class MatchService:
    """
    Service responsible for football match business logic.
    """

    def __init__(self, db: Session):
        self.repository = MatchRepository(db)

    def _to_upcoming_match_response(
        self,
        match,
    ) -> UpcomingMatchResponse:
        """
        Convert a Match model into an
        UpcomingMatchResponse schema.
        """

        return UpcomingMatchResponse(
            id=match.id,
            competition_id=match.competition_id,
            competition_name=(
                match.competition.name
                if match.competition
                else None
            ),
            competition_code=(
                match.competition.code
                if match.competition
                else None
            ),
            competition_emblem=(
                match.competition.emblem
                if match.competition
                else None
            ),
            home_team_id=match.home_team_id,
            home_team_name=(
                match.home_team.name
                if match.home_team
                else None
            ),
            home_team_crest=(
                match.home_team.crest
                if match.home_team
                else None
            ),
            away_team_id=match.away_team_id,
            away_team_name=(
                match.away_team.name
                if match.away_team
                else None
            ),
            away_team_crest=(
                match.away_team.crest
                if match.away_team
                else None
            ),
            utc_date=match.utc_date,
            status=match.status,
            match_week=match.match_week,
        )

    def get_match(
        self,
        match_id: int,
    ) -> MatchDetailResponse | None:

        match = self.repository.get_match_by_id(match_id)

        if match is None:
            return None

        return MatchDetailResponse(
            id=match.id,
            competition_id=match.competition_id,
            competition_name=(
                match.competition.name
                if match.competition
                else None
            ),
            competition_code=(
                match.competition.code
                if match.competition
                else None
            ),
            competition_emblem=(
                match.competition.emblem
                if match.competition
                else None
            ),
            home_team_id=match.home_team_id,
            home_team_name=(
                match.home_team.name
                if match.home_team
                else None
            ),
            home_team_crest=(
                match.home_team.crest
                if match.home_team
                else None
            ),
            away_team_id=match.away_team_id,
            away_team_name=(
                match.away_team.name
                if match.away_team
                else None
            ),
            away_team_crest=(
                match.away_team.crest
                if match.away_team
                else None
            ),
            utc_date=match.utc_date,
            status=match.status,
            home_score=match.home_score,
            away_score=match.away_score,
            match_week=match.match_week,
        )

    def get_upcoming_matches(
        self,
        limit: int | None = None,
    ) -> list[UpcomingMatchResponse]:

        matches = self.repository.get_upcoming_matches(
            limit=limit
        )

        return [
            self._to_upcoming_match_response(match)
            for match in matches
        ]

    def get_next_match(self):
        match = self.repository.get_next_match()
        return self._to_upcoming_match_response(match) if match else None

    def get_today_matches(
        self,
        today: datetime,
    ):
        return self.repository.get_today_matches(today)

    def get_upcoming_matches_by_competition(
        self,
        competition_id: int,
        limit: int | None = None,
    ) -> list[UpcomingMatchResponse]:
        matches = self.repository.get_upcoming_matches_by_competition(
            competition_id,
            limit,
        )
        return [
            self._to_upcoming_match_response(match)
            for match in matches
        ]

    def get_upcoming_matches_by_date(
        self,
        match_date: datetime,
    ) -> list[UpcomingMatchResponse]:

        matches = self.repository.get_upcoming_matches_by_date(
            match_date,
        )

        return [
            self._to_upcoming_match_response(match)
            for match in matches
        ]
    
    def get_matches_by_date(
        self,
        match_date: datetime,
        status: str | None = None,
    ) -> list[MatchDetailResponse]:
        """
        Return matches for a specific date.

        If status is provided,
        only matches with that status are returned.
        """

        matches = self.repository.get_matches_by_date(
            match_date=match_date,
            status=status,
        )

        return [
            MatchDetailResponse(
                id=match.id,
                competition_id=match.competition_id,
                competition_name=(
                    match.competition.name
                    if match.competition
                    else None
                ),
                competition_code=(
                    match.competition.code
                    if match.competition
                    else None
                ),
                competition_emblem=(
                    match.competition.emblem
                    if match.competition
                    else None
                ),
                home_team_id=match.home_team_id,
                home_team_name=(
                    match.home_team.name
                    if match.home_team
                    else None
                ),
                home_team_crest=(
                    match.home_team.crest
                    if match.home_team
                    else None
                ),
                away_team_id=match.away_team_id,
                away_team_name=(
                    match.away_team.name
                    if match.away_team
                    else None
                ),
                away_team_crest=(
                    match.away_team.crest
                    if match.away_team
                    else None
                ),
                utc_date=match.utc_date,
                status=match.status,
                home_score=match.home_score,
                away_score=match.away_score,
                match_week=match.match_week,
            )
            for match in matches
        ]

    def search_matches_by_team(self, search_term: str, status: str | None = "SCHEDULED") -> list[MatchDetailResponse]:
        matches = self.repository.search_matches_by_team(search_term, status)
        # Reuse the single, detailed response mapper so searched fixtures have
        # exactly the same fields as calendar fixtures.
        return [self.get_match(match.id) for match in matches]

    def get_competition_matchweeks(self, competition_id: int, status: str | None = "SCHEDULED") -> list[int]:
        return self.repository.get_competition_matchweeks(competition_id, status)

    def get_matches_by_matchweek(self, competition_id: int, match_week: int, status: str | None = "SCHEDULED") -> list[MatchDetailResponse]:
        return [self.get_match(match.id) for match in self.repository.get_matches_by_matchweek(competition_id, match_week, status)]
    
    def get_matches_between_dates(
        self,
        start_date: datetime,
        end_date: datetime,
    ):
        return self.repository.get_matches_between_dates(
            start_date,
            end_date,
        )

    def get_latest_match_date(
        self,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the latest available match date.

        Optionally filtered by status.
        """

        return self.repository.get_latest_match_date(
            status=status,
        )

    def get_previous_match_date(
        self,
        current_date: datetime,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the closest previous match date.

        Only dates containing matches are returned.
        """

        return self.repository.get_previous_match_date(
            current_date=current_date,
            status=status,
        )

    def get_next_match_date(
        self,
        current_date: datetime,
        status: str | None = None,
    ) -> datetime | None:
        """
        Return the closest next match date.

        Only dates containing matches are returned.
        """

        return self.repository.get_next_match_date(
            current_date=current_date,
            status=status,
        )
