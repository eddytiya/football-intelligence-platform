from app.db.session import SessionLocal
from app.services.etl.daily_etl_pipeline import DailyETLPipeline


def main():

    print("=" * 60)
    print("Starting Daily Football ETL Pipeline")
    print("=" * 60)

    db = SessionLocal()

    try:

        pipeline = DailyETLPipeline(db)

        pipeline.run()

        print("\n" + "=" * 60)
        print("Daily Football ETL Pipeline Finished Successfully")
        print("=" * 60)

    except Exception as e:

        print(f"\nPipeline Failed: {e}")
        raise

    finally:

        db.close()

        print("\nDatabase session closed.")


if __name__ == "__main__":
    main()