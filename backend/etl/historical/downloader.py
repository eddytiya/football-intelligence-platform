from pathlib import Path

import httpx
from loguru import logger


class HistoricalDownloader:
    """
    Downloads historical football datasets from football-data.co.uk.

    Responsibilities
    ----------------
    - Generate download URLs
    - Download CSV files
    - Save CSVs locally
    """

    BASE_URL = "https://www.football-data.co.uk/mmz4281"

    LEAGUES = {
        "PL": "E0",     # Premier League
        "PD": "SP1",    # La Liga
        "SA": "I1",     # Serie A
        "BL1": "D1",    # Bundesliga
        "FL1": "F1",    # Ligue 1
        "DED": "N1",    # Eredivisie
        "PPL": "P1",    # Primeira Liga
        "ELC": "E1",    # Championship
    }

    def __init__(
        self,
        output_dir: str = "data/raw/historical",
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = httpx.Client(timeout=60)

    def build_season_code(
        self,
        season: int,
    ) -> str:
        """
        Convert season year into football-data.co.uk format.

        Example
        -------
        2010 -> 1011
        2016 -> 1617
        2025 -> 2526
        """

        start = str(season)[-2:]
        end = str(season + 1)[-2:]

        return f"{start}{end}"

    def build_url(
        self,
        league_code: str,
        season: int,
    ) -> str:

        season_code = self.build_season_code(season)

        return (
            f"{self.BASE_URL}/"
            f"{season_code}/"
            f"{league_code}.csv"
        )

    def download_file(
        self,
        competition: str,
        league_code: str,
        season: int,
    ) -> bool:

        url = self.build_url(
            league_code,
            season,
        )

        filename = (
            f"{competition}_{season}.csv"
        )

        filepath = self.output_dir / filename

        if filepath.exists():

            logger.info(
                f"Already exists: {filename}"
            )

            return True

        logger.info(
            f"Downloading {filename}"
        )

        try:

            response = self.client.get(url)

            response.raise_for_status()

            filepath.write_bytes(
                response.content
            )

            logger.success(
                f"Downloaded {filename}"
            )

            return True

        except Exception as e:

            logger.error(
                f"Failed to download "
                f"{filename}: {e}"
            )

            return False

    def download_all(
        self,
        start_season: int = 2010,
        end_season: int = 2025,
    ):

        logger.info("=" * 70)
        logger.info("Historical Dataset Downloader")
        logger.info("=" * 70)

        downloaded = 0
        failed = 0

        for competition, league_code in self.LEAGUES.items():

            logger.info(
                f"Competition: {competition}"
            )

            for season in range(
                start_season,
                end_season + 1,
            ):

                success = self.download_file(
                    competition,
                    league_code,
                    season,
                )

                if success:
                    downloaded += 1
                else:
                    failed += 1

        logger.success(
            f"Finished. "
            f"Downloaded={downloaded}, "
            f"Failed={failed}"
        )

    def close(self):

        self.client.close()


def main():

    downloader = HistoricalDownloader()

    try:

        downloader.download_all()

    finally:

        downloader.close()


if __name__ == "__main__":

    main()