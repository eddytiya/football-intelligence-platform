from pathlib import Path
from typing import Dict

import pandas as pd
from loguru import logger


class HistoricalExtractor:
    """
    Extracts historical football datasets from downloaded CSV files.

    Responsibilities
    ----------------
    - Locate CSV files
    - Read CSV files
    - Validate files
    - Return pandas DataFrames
    """

    def __init__(
        self,
        data_dir: str = "data/raw/historical",
    ):
        self.data_dir = Path(data_dir)

    def get_csv_files(self):
        """
        Returns all CSV files sorted alphabetically.
        """

        files = sorted(self.data_dir.glob("*.csv"))

        logger.info(f"Found {len(files)} CSV files.")

        return files

    def extract_file(
        self,
        filepath: Path,
    ) -> pd.DataFrame:
        """
        Read a single CSV file.
        """

        logger.info(f"Reading {filepath.name}")

        try:

            df = pd.read_csv(filepath)

            logger.success(
                f"{filepath.name} -> {len(df)} matches"
            )

            return df

        except Exception as e:

            logger.error(
                f"Failed reading {filepath.name}: {e}"
            )

            return pd.DataFrame()

    def extract_all(
        self,
    ) -> Dict[str, pd.DataFrame]:
        """
        Read every CSV file.

        Returns
        -------
        Dictionary:

        {
            "PL_2010": dataframe,
            "PL_2011": dataframe,
            ...
        }
        """

        datasets = {}

        files = self.get_csv_files()

        for file in files:

            df = self.extract_file(file)

            if df.empty:

                logger.warning(
                    f"Skipping empty file {file.name}"
                )

                continue

            datasets[file.stem] = df

        logger.success(
            f"Loaded {len(datasets)} datasets."
        )

        return datasets


def main():

    extractor = HistoricalExtractor()

    datasets = extractor.extract_all()

    print("\n")
    print("=" * 70)
    print("Historical Dataset Summary")
    print("=" * 70)

    for name, df in datasets.items():

        print(f"{name:15} {len(df):5} matches")


if __name__ == "__main__":

    main()