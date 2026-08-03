from app.db.session import SessionLocal
from app.repositories.sync_repository import SyncRepository
from app.services.sync.sync_service import SyncService


def main():

    db = SessionLocal()

    try:

        repository = SyncRepository(db)

        service = SyncService(repository)

        start, end = service.get_sync_window(
            provider="football-data",
            resource="matches",
        )

        print("=" * 60)
        print("Sync Window")
        print("=" * 60)
        print(f"Start : {start}")
        print(f"End   : {end}")

    finally:
        db.close()


if __name__ == "__main__":
    main()