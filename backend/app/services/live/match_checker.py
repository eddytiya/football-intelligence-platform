from datetime import date, timedelta

from app.services.football_api import FootballAPIClient


class MatchChecker:
    """
    Checks the Football Data API to determine
    whether live synchronization should run.
    """

    def __init__(self):

        self.api = FootballAPIClient()

    def should_sync(self) -> bool:
        """
        Returns True if there are matches
        yesterday, today or tomorrow.
        """

        today = date.today()

        date_from = (today - timedelta(days=1)).isoformat()
        date_to = (today + timedelta(days=1)).isoformat()

        print(f"\nChecking fixtures from {date_from} to {date_to}...")

        response = self.api.get(
            endpoint="/matches",
            params={
                "dateFrom": date_from,
                "dateTo": date_to,
            },
        )

        if not response:
            print("Unable to retrieve fixtures.")
            return False

        matches = response.get("matches", [])

        print(f"Matches found : {len(matches)}")

        return len(matches) > 0