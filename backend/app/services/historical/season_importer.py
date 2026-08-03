from sqlalchemy.orm import Session

from app.repositories.match_repository import MatchRepository
from app.services.historical.historical_importer import HistoricalImporter
from etl.utils.logger import logger


class SeasonImporter:
    """
    Imports a complete season into the database.

    Responsibilities
    ----------------
    - Download historical matches
    - Check existing matches
    - Insert new matches
    - Update existing matches
    """

    def __init__(self, db: Session):
        self.db = db
        self.importer = HistoricalImporter()
        self.match_repository = MatchRepository(db)

    def import_season(
        self,
        competition_code: str,
        season: int,
    ):
        """
        Import one season.
        """

        logger.info(
            f"Starting {competition_code} {season}"
        )

        matches = self.importer.import_matches(
            competition_code=competition_code,
            start_season=season,
            end_season=season,
        )

        logger.info(
            f"Fetched {len(matches)} matches"
        )

        inserted = 0
        updated = 0

        for match in matches:

            existing_match = self.match_repository.get_by_api_id(
                match["id"]
            )

            if existing_match:

                self.match_repository.update_from_api(
                    existing_match,
                    match,
                )

                updated += 1

            else:

                self.match_repository.create_from_api(
                    match
                )

                inserted += 1

        self.db.commit()

        logger.info(
            f"Season {season} complete"
        )

        logger.info(
            f"Inserted : {inserted}"
        )

        logger.info(
            f"Updated  : {updated}"
        )

    def close(self):
        self.importer.close()