from app.db.session import SessionLocal
from app.services.etl.incremental_match_etl import IncrementalMatchETL


def main():
    """
    Test runner for Incremental Match ETL.
    """

    db = SessionLocal()

    try:
        print("=" * 60)
        print("Starting Incremental Match ETL")
        print("=" * 60)

        etl = IncrementalMatchETL(db)
        etl.run()

        print()
        print("=" * 60)
        print("Incremental Match ETL Completed Successfully")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("Incremental Match ETL Failed")
        print("=" * 60)
        print(f"Error: {e}")
        raise

    finally:
        db.close()
        print("\nDatabase session closed.")


if __name__ == "__main__":
    main()