import time

from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.repositories.competition_repository import CompetitionRepository
from app.repositories.sync_repository import SyncRepository
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.services.sync.sync_service import SyncService
from app.utils.etl_helpers import update_if_changed


class IncrementalCompetitionETL:
    """
    Incremental ETL pipeline for competitions.
    """

    PROVIDER = "football-data"
    RESOURCE = "competitions"

    def __init__(self, db: Session):
        self.db = db

        self.client = FootballAPIClient()

        self.repository = CompetitionRepository(db)

        self.sync_service = SyncService(
            SyncRepository(db)
        )

    # =====================================================
    # EXTRACT
    # =====================================================

    def extract(self):
        """
        Extract competitions from Football-Data API.
        """

        print("\nExtracting competitions...")

        return self.client.get("/competitions")

    # =====================================================
    # TRANSFORM
    # =====================================================

    def transform(self, data):

        competitions = []

        if not data:
            return competitions

        for item in data.get("competitions", []):

            area = item.get("area") or {}

            required = [
                item.get("id"),
                item.get("name"),
                item.get("code"),
                item.get("type"),
                area.get("name"),
                area.get("code"),
            ]

            if any(
                value is None
                or (
                    isinstance(value, str)
                    and not value.strip()
                )
                for value in required
            ):
                continue

            competitions.append(
                Competition(
                    api_id=item.get("id"),
                    name=item.get("name"),
                    code=item.get("code"),
                    type=item.get("type"),
                    area_name=area.get("name"),
                    area_code=area.get("code"),
                    area_flag=area.get("flag"),
                    emblem=item.get("emblem"),
                    seasons_available=item.get(
                        "numberOfAvailableSeasons"
                    ),
                )
            )

        return competitions

    # =====================================================
    # RUN
    # =====================================================

    def run(self):

        print(
            "\n=============================================="
        )
        print("Incremental Competition ETL")
        print(
            "==============================================\n"
        )

        start_time = time.time()

        sync_log = self.sync_service.create_sync_log(
            provider=self.PROVIDER,
            resource=self.RESOURCE,
        )

        processed = 0
        inserted = 0
        updated = 0
        skipped = 0

        try:

            window_start, window_end = (
                self.sync_service.get_sync_window(
                    provider=self.PROVIDER,
                    resource=self.RESOURCE,
                )
            )

            print(
                f"Sync Window : "
                f"{window_start} -> {window_end}"
            )

            data = self.extract()

            competitions = self.transform(data)

            print(
                f"\nFetched {len(competitions)} competitions.\n"
            )

            for competition in competitions:

                processed += 1

                print(
                    f"Processing : {competition.name}"
                )

                existing = (
                    self.repository.get_by_api_id(
                        competition.api_id
                    )
                )
            if existing is None:

                    self.db.add(competition)
                    self.db.flush()

                    MappingService.save_mapping(
                        db=self.db,
                        entity_type="competition",
                        provider="football-data",
                        entity_id=competition.id,
                        external_id=competition.api_id,
                    )

                    inserted += 1

                    print(
                        f"  CREATED -> {competition.name}"
                    )

            else:

                    changed = update_if_changed(
                        existing,
                        competition,
                        [
                            "name",
                            "code",
                            "type",
                            "area_name",
                            "area_code",
                            "area_flag",
                            "emblem",
                            "seasons_available",
                        ],
                    )

                    MappingService.save_mapping(
                        db=self.db,
                        entity_type="competition",
                        provider="football-data",
                        entity_id=existing.id,
                        external_id=existing.api_id,
                    )

                    if changed:

                        updated += 1

                        print(
                            f"  UPDATED -> {competition.name}"
                        )

                    else:

                        skipped += 1

                        print(
                            f"  SKIPPED -> {competition.name}"
                        )

            self.db.commit()

            duration = round(
                time.time() - start_time,
                2,
            )

            self.sync_service.complete_sync(
                sync_log=sync_log,
                processed=processed,
                inserted=inserted,
                updated=updated,
                duration=duration,
            )

            print("\n========================================")
            print("Incremental Competition ETL Summary")
            print("========================================")
            print(f"Processed : {processed}")
            print(f"Created   : {inserted}")
            print(f"Updated   : {updated}")
            print(f"Skipped   : {skipped}")
            print(f"Duration  : {duration} sec")
            print("========================================")

        except Exception as e:

            self.db.rollback()

            duration = round(
                time.time() - start_time,
                2,
            )

            self.sync_service.fail_sync(
                sync_log=sync_log,
                duration=duration,
            )

            print("\nCompetition ETL failed.")
            print(e)

            raise

        finally:

            self.db.close()


if __name__ == "__main__":

    from app.db.session import SessionLocal

    db = SessionLocal()

    try:

        IncrementalCompetitionETL(db).run()

    finally:

        db.close()