from app.services.etl.season_etl import SeasonETL


def main():
    """
    Entry point for running the Season ETL.
    """

    print("Starting Season ETL...\n")

    etl = SeasonETL()

    etl.run()

    print("\nSeason ETL finished successfully.")


if __name__ == "__main__":
    main()