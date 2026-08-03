from app.db.session import SessionLocal
from app.services.etl.daily_etl_pipeline import DailyETLPipeline


def main():

    db = SessionLocal()

    try:

        pipeline = DailyETLPipeline(db)
        pipeline.run()

    finally:

        db.close()


if __name__ == "__main__":
    main()