from app.models.match import Match
from app.services.mapping_service import MappingService
from app.utils.datetime_parser import parse_datetime
from app.services.matching.result_validation import validate_provider_match


class MatchMapper:
    """
    Maps Football-Data.org matches to the internal Match model.
    """

    PROVIDER = "football-data"

    def __init__(self, db):
        self.db = db

    def create(
        self,
        match_data: dict,
    ) -> Match:
        """
        Create a new Match object from API data.
        """

        validate_provider_match(match_data)
        utc_date = parse_datetime(
            match_data["utcDate"]
        )

        return Match(
            api_id=str(match_data["id"]),
            competition_id=self._competition_id(match_data),
            season_id=self._season_id(match_data),
            home_team_id=self._home_team_id(match_data),
            away_team_id=self._away_team_id(match_data),
            utc_date=utc_date,
            match_date=utc_date.date(),
            kick_off=utc_date.time(),
            status=match_data["status"],
            match_week=match_data.get("matchday"),
            stage=match_data.get("stage"),
            home_score=self._home_score(match_data),
            away_score=self._away_score(match_data),
        )

    def update(
        self,
        match: Match,
        match_data: dict,
    ) -> Match:
        """
        Update an existing Match.
        """

        validate_provider_match(match_data)
        utc_date = parse_datetime(
            match_data["utcDate"]
        )

        match.competition_id = self._competition_id(
            match_data
        )

        match.season_id = self._season_id(
            match_data
        )

        match.home_team_id = self._home_team_id(
            match_data
        )

        match.away_team_id = self._away_team_id(
            match_data
        )

        match.utc_date = utc_date
        match.match_date = utc_date.date()
        match.kick_off = utc_date.time()

        match.status = match_data["status"]
        match.match_week = match_data.get("matchday")
        match.stage = match_data.get("stage")

        match.home_score = self._home_score(
            match_data
        )

        match.away_score = self._away_score(
            match_data
        )

        return match

    # ======================================================
    # Internal Mapping Helpers
    # ======================================================

    def _competition_id(
        self,
        match_data: dict,
    ) -> int:

        return MappingService.require_internal_id(
            db=self.db,
            entity_type="competition",
            provider=self.PROVIDER,
            external_id=match_data["competition"]["id"],
        )

    def _season_id(
        self,
        match_data: dict,
    ) -> int:

        return MappingService.require_internal_id(
            db=self.db,
            entity_type="season",
            provider=self.PROVIDER,
            external_id=match_data["season"]["id"],
        )

    def _home_team_id(
        self,
        match_data: dict,
    ) -> int:

        return MappingService.require_internal_id(
            db=self.db,
            entity_type="team",
            provider=self.PROVIDER,
            external_id=match_data["homeTeam"]["id"],
        )

    def _away_team_id(
        self,
        match_data: dict,
    ) -> int:

        return MappingService.require_internal_id(
            db=self.db,
            entity_type="team",
            provider=self.PROVIDER,
            external_id=match_data["awayTeam"]["id"],
        )

    @staticmethod
    def _home_score(
        match_data: dict,
    ) -> int:

        score = match_data["score"]["fullTime"]["home"]

        return score if score is not None else 0

    @staticmethod
    def _away_score(
        match_data: dict,
    ) -> int:

        score = match_data["score"]["fullTime"]["away"]

        return score if score is not None else 0
