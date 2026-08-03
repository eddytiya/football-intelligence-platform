from app.services.etl.competition_etl import CompetitionETL


def main():
    """
    Entry point for running the Competition ETL.
    """

    print("Starting Competition ETL...\n")

    etl = CompetitionETL()

    etl.run()

    print("\nCompetition ETL finished successfully.")


if __name__ == "__main__":
    main()