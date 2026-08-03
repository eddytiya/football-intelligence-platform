from etl.config.settings import settings
from etl.extract.api_client import APIClient


class FootballDataExtractor:
    """
    Wrapper around Football-Data.org API.
    """

    def __init__(self):
        self.client = APIClient(
            base_url=settings.FOOTBALL_API_BASE_URL,
            headers={
                "X-Auth-Token": settings.FOOTBALL_API_KEY,
            },
        )

    def get_competitions(self):
        """
        Fetch all competitions.
        """
        return self.client.get("/competitions")

    def get_competition(self, competition_code: str):
        """
        Fetch details for a competition.
        """
        return self.client.get(
            f"/competitions/{competition_code}"
        )

    def get_teams(
        self,
        competition_code: str,
        season: int | None = None,
    ):
        """
        Fetch all teams for a competition.
        Optionally fetch teams for a specific season.
        """
        params = {}

        if season is not None:
            params["season"] = season

        return self.client.get(
            f"/competitions/{competition_code}/teams",
            params=params or None,
        )

    def get_matches(
        self,
        competition_code: str,
        season: int | None = None,
        status: str | None = None,
        matchday: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        """
        Fetch matches for a competition.

        Optional filters:
        - season
        - status
        - matchday
        - dateFrom
        - dateTo
        """
        params = {}

        if season is not None:
            params["season"] = season

        if status is not None:
            params["status"] = status

        if matchday is not None:
            params["matchday"] = matchday

        if date_from is not None:
            params["dateFrom"] = date_from

        if date_to is not None:
            params["dateTo"] = date_to

        return self.client.get(
            f"/competitions/{competition_code}/matches",
            params=params or None,
        )

    def get_match(self, match_id: int):
        """
        Fetch details for a single match.
        """
        return self.client.get(
            f"/matches/{match_id}"
        )

    def get_standings(
        self,
        competition_code: str,
        season: int | None = None,
    ):
        """
        Fetch standings for a competition.
        Optionally fetch standings for a specific season.
        """
        params = {}

        if season is not None:
            params["season"] = season

        return self.client.get(
            f"/competitions/{competition_code}/standings",
            params=params or None,
        )

    def close(self):
        self.client.close()