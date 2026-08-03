from app.services.etl.competition_team_etl import (
    CompetitionTeamETL,
)


def main():

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Competition Team ETL Test")
    print("=" * 70)

    try:

        print("\nInitializing ETL...")

        etl = CompetitionTeamETL()

        print("✓ ETL initialized successfully.")

        print("\nRunning Competition Team ETL...\n")

        etl.run()

        print("\n✓ Competition Team ETL completed successfully.")

    except Exception as e:

        print("\n✗ Competition Team ETL failed.")

        print(e)

        raise


if __name__ == "__main__":
    main()