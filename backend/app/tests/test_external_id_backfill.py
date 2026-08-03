from app.db.session import SessionLocal
from app.services.matching.external_id_backfill import ExternalIDBackfill


def main():
    db = SessionLocal()

    try:
        backfill = ExternalIDBackfill(db)
        backfill.run()

    finally:
        db.close()


if __name__ == "__main__":
    main()