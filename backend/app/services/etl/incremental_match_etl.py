from datetime import timedelta
import time
import traceback

from sqlalchemy.orm import Session

from app.repositories.match_repository import MatchRepository
from app.repositories.sync_repository import SyncRepository
from app.services.football_api import FootballAPIClient
from app.services.matching.match_mapper import MatchMapper
from app.services.matching.match_resolver import MatchResolver
from app.services.sync.sync_service import SyncService


class IncrementalMatchETL:
    """
    Incremental ETL pipeline for football matches.
    """

    def __init__(self, db: Session):
        self.db = db

        self.api_client = FootballAPIClient()

        self.match_repository = MatchRepository(db)

        self.sync_repository = SyncRepository(db)

        self.sync_service = SyncService(
            self.sync_repository
        )

        self.match_resolver = MatchResolver(db)

        self.match_mapper = MatchMapper(db)

    def run(self):
        """
        Execute an incremental synchronization.
        """

        start, end = self.sync_service.get_sync_window(
            provider="football-data",
            resource="matches",
        )

        print("=" * 60)
        print("Incremental Match ETL")
        print("=" * 60)
        print(f"Sync Start : {start}")
        print(f"Sync End   : {end}")

        processed = 0
        created = 0
        updated = 0
        skipped = 0

        start_time = time.perf_counter()

        sync_log = self.sync_service.create_sync_log(
            provider="football-data",
            resource="matches",
        )

        try:

            current_date = start.date()
            end_date = end.date()

            while current_date <= end_date:

                print("\n" + "-" * 60)
                print(f"Syncing Date : {current_date}")
                print("-" * 60)

                params = {
                    "dateFrom": current_date.strftime("%Y-%m-%d"),
                    "dateTo": current_date.strftime("%Y-%m-%d"),
                }

                data = self.api_client.get(
                    "/matches",
                    params=params,
                )

                if data is None:
                    print("No data returned.")
                    current_date += timedelta(days=1)
                    continue

                matches = data.get("matches", [])

                print(f"Downloaded {len(matches)} matches.")

                for match_data in matches:

                    try:

                        api_id = str(match_data["id"])

                        existing = self.match_repository.get_match_by_api_id(
                            api_id
                        )

                        if existing:

                            print(f"UPDATE -> {api_id}")

                            self.match_mapper.update(
                                existing,
                                match_data,
                            )

                            self.match_repository.update_match(
                                existing,
                            )

                            updated += 1

                        else:

                            print(f"CREATE -> {api_id}")

                            match = self.match_mapper.create(
                                match_data,
                            )

                            self.match_repository.create_match(
                                match,
                            )

                            created += 1

                        processed += 1

                    except Exception:

                        self.db.rollback()

                        skipped += 1

                        print("\n" + "=" * 80)
                        print(f"FAILED MATCH : {match_data.get('id')}")
                        traceback.print_exc()
                        print("=" * 80 + "\n")

                current_date += timedelta(days=1)

            duration = time.perf_counter() - start_time

            self.sync_service.complete_sync(
                sync_log=sync_log,
                processed=processed,
                inserted=created,
                updated=updated,
                duration=duration,
            )

        except Exception:

            self.db.rollback()

            duration = time.perf_counter() - start_time

            self.sync_service.fail_sync(
                sync_log=sync_log,
                duration=duration,
            )

            raise

        print()
        print("=" * 60)
        print("Incremental Match ETL Summary")
        print("=" * 60)
        print(f"Processed : {processed}")
        print(f"Created   : {created}")
        print(f"Updated   : {updated}")
        print(f"Skipped   : {skipped}")
        print(f"Duration  : {duration:.2f} seconds")
        print("=" * 60)