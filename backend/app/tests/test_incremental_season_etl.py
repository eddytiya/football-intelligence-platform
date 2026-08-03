from app.db.session import SessionLocal
from app.services.etl.incremental_season_etl import (
    IncrementalSeasonETL,
)


def main():

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Incremental Season ETL Test")
    print("=" * 70)

    db = SessionLocal()

    try:

        print("\nInitializing ETL...")

        etl = IncrementalSeasonETL(db)

        print("✓ ETL initialized successfully.")

        print("\nRunning Incremental Season ETL...\n")

        etl.run()

        print("\n✓ Incremental Season ETL completed successfully.")

    except Exception as e:

        print("\n✗ Incremental Season ETL failed.")

        print(e)

        raise

    finally:

        db.close()

        print("\n✓ Database session closed.")


if __name__ == "__main__":
    main()