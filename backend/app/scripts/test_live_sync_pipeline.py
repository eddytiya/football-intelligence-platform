from app.db.session import SessionLocal
from app.services.live.live_sync_pipeline import LiveSyncPipeline


def main():

    db = SessionLocal()

    try:
        pipeline = LiveSyncPipeline(db)
        pipeline.run()

    finally:
        db.close()


if __name__ == "__main__":
    main()