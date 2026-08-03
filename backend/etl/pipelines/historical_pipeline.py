from datetime import datetime

from loguru import logger

from etl.load.load_matches import MatchLoader


class HistoricalPipeline:
    """
    Historical Match Import Pipeline.

    Responsibilities
    ----------------
    - Import historical matches
    - Iterate through seasons
    - Reuse MatchLoader
    """

    def __init__(
        self,
        start_season: int = 2016,
        end_season: int | None = None,
    ):
        self.start_season = start_season
        self.end_season = (
            end_season
            if end_season is not None
            else datetime.now().year
        )

        self.loader = MatchLoader()

    def run(self):
        """
        Run the historical import.
        """

        logger.info("=" * 70)
        logger.info("Historical Match Import")
        logger.info("=" * 70)

        logger.info(
            f"Importing seasons "
            f"{self.start_season} "
            f"to "
            f"{self.end_season}"
        )

        try:

            for season in range(
                self.start_season,
                self.end_season + 1,
            ):

                logger.info("")
                logger.info("-" * 60)
                logger.info(
                    f"Season {season}"
                )
                logger.info("-" * 60)

                self.loader.load_matches(
                    season=season
                )

            logger.success(
                "Historical Import Completed."
            )

        except Exception:

            logger.exception(
                "Historical Import Failed."
            )

        finally:

            self.loader.close()


def main():

    pipeline = HistoricalPipeline()

    pipeline.run()


if __name__ == "__main__":

    main()