from app.db.session import SessionLocal
from app.services.etl.incremental_competition_etl import (
    IncrementalCompetitionETL,
)


def main():

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Incremental Competition ETL Test")
    print("=" * 70)

    db = SessionLocal()

    try:

        print("\nInitializing ETL...")

        etl = IncrementalCompetitionETL(db)

        print("✓ ETL initialized successfully.")

        print("\nRunning Incremental Competition ETL...\n")

        etl.run()

        print("\n✓ Incremental Competition ETL completed successfully.")

    except Exception as e:

        print("\n✗ ETL failed.")

        print(e)

        raise

    finally:

        db.close()

        print("\n✓ Database session closed.")


if __name__ == "__main__":
    main()