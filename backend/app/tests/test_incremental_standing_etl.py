from app.db.session import SessionLocal
from app.services.etl.incremental_standing_etl import (
    IncrementalStandingETL,
)


def main():

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Incremental Standing ETL Test")
    print("=" * 70)

    db = SessionLocal()

    try:

        print("\nInitializing ETL...")

        etl = IncrementalStandingETL(db)

        print("✓ ETL initialized successfully.")

        print("\nRunning Incremental Standing ETL...\n")

        etl.run()

        print(
            "\n✓ Incremental Standing ETL completed successfully."
        )

    except Exception as e:

        print(
            "\n✗ Incremental Standing ETL failed."
        )

        print(e)

        raise

    finally:

        db.close()

        print("\n✓ Database session closed.")


if __name__ == "__main__":
    main()