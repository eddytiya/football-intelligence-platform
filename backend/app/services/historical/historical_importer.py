from typing import Any

from etl.extract.football_data import FootballDataExtractor
from etl.utils.logger import logger


class HistoricalImporter:
    """
    Imports historical football data from Football-Data.org.

    Responsibilities
    ----------------
    - Fetch matches for historical seasons
    - Combine multiple seasons into one dataset
    - Return raw API data
    """

    def __init__(self):
        self.extractor = FootballDataExtractor()

    def import_matches(
        self,
        competition_code: str,
        start_season: int,
        end_season: int,
    ) -> list[dict[str, Any]]:
        """
        Import matches from a range of seasons.

        Example:
            import_matches("PL", 2016, 2026)
        """

        all_matches = []

        logger.info(
            f"Importing {competition_code} "
            f"from {start_season} to {end_season}"
        )

        for season in range(start_season, end_season + 1):

            logger.info(f"Fetching season {season}")

            response = self.extractor.get_matches(
                competition_code=competition_code,
                season=season,
            )

            matches = response.get("matches", [])

            logger.info(
                f"Season {season}: "
                f"{len(matches)} matches"
            )

            all_matches.extend(matches)

        logger.info(
            f"Imported {len(all_matches)} total matches"
        )

        return all_matches

    def close(self):
        self.extractor.close()