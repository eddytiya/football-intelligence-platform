from app.db.session import SessionLocal
from app.services.etl.incremental_team_etl import IncrementalTeamETL


def main():
    """
    Test Incremental Team ETL.
    """

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Incremental Team ETL Test")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:

        etl = IncrementalTeamETL(db)

        etl.run()

        print()
        print("✓ Incremental Team ETL completed successfully.")

    except Exception as e:

        print()
        print("✗ Incremental Team ETL failed.")
        print(e)

        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()