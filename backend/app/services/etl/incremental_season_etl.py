import time

from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.season import Season
from app.repositories.season_repository import SeasonRepository
from app.repositories.sync_repository import SyncRepository
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.services.sync.sync_service import SyncService
from app.utils.date_parser import parse_date
from app.utils.etl_helpers import update_if_changed


class IncrementalSeasonETL:
    """
    Incremental ETL pipeline responsible for
    synchronizing Season data.
    """

    PROVIDER = "football-data"
    RESOURCE = "seasons"

    def __init__(self, db: Session):

        self.db = db

        self.client = FootballAPIClient()

        self.repository = SeasonRepository(db)

        self.sync_service = SyncService(
            SyncRepository(db)
        )

    # ==================================================
    # Extract
    # ==================================================

    def extract(self):

        print("\nExtracting seasons...")

        return self.client.get("/competitions")

    # ==================================================
    # Transform
    # ==================================================

    def transform(self, data):

        seasons = []

        if not data:
            return seasons

        for competition in data.get("competitions", []):

            current_season = competition.get(
                "currentSeason"
            )

            if not current_season:
                continue

            if competition.get("id") is None:
                continue

            if current_season.get("id") is None:
                continue

            start_date = parse_date(
                current_season.get("startDate")
            )

            end_date = parse_date(
                current_season.get("endDate")
            )

            if start_date and end_date:

                if start_date.year == end_date.year:

                    season_name = str(
                        start_date.year
                    )

                else:

                    season_name = (
                        f"{start_date.year}/"
                        f"{str(end_date.year)[2:]}"
                    )

            else:

                season_name = None

            season = Season(

                api_id=current_season.get("id"),

                competition_id=None,

                season_name=season_name,

                start_year=(
                    start_date.year
                    if start_date
                    else None
                ),

                end_year=(
                    end_date.year
                    if end_date
                    else None
                ),

                start_date=start_date,

                end_date=end_date,

                current_matchday=current_season.get(
                    "currentMatchday"
                ),

                winner_team_id=None,
            )

            # Temporary attribute
            season.competition_api_id = (
                competition.get("id")
            )

            seasons.append(season)

        return seasons

    # ==================================================
    # Run
    # ==================================================

    def run(self):

        print(
            "\n========================================"
        )
        print(
            "Incremental Season ETL"
        )
        print(
            "========================================"
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
                f"\nSync Window : "
                f"{window_start} -> {window_end}"
            )

            data = self.extract()

            seasons = self.transform(data)

            print(
                f"\nFetched {len(seasons)} seasons.\n"
            )

            competitions = {

                competition.api_id: competition.id

                for competition in self.db.query(
                    Competition
                ).all()

            }

            for season in seasons:

                processed += 1

                competition_id = competitions.get(
                    season.competition_api_id
                )

                if competition_id is None:

                    print(
                        f"Competition "
                        f"{season.competition_api_id}"
                        f" not found."
                    )

                    continue

                season.competition_id = (
                    competition_id
                )

                existing = (
                    self.repository
                    .get_season_by_api_id(
                        season.api_id
                    )
                )

                if existing is None:

                    self.db.add(season)

                    self.db.flush()

                    MappingService.save_mapping(
                        db=self.db,
                        entity_type="season",
                        provider="football-data",
                        entity_id=season.id,
                        external_id=season.api_id,
                    )

                    inserted += 1

                    print(
                        f"CREATED -> {season.season_name}"
                    )

                else:

                    changed = update_if_changed(
                        existing,
                        season,
                        [
                            "competition_id",
                            "season_name",
                            "start_year",
                            "end_year",
                            "start_date",
                            "end_date",
                            "current_matchday",
                            "winner_team_id",
                        ],
                    )

                    MappingService.save_mapping(
                        db=self.db,
                        entity_type="season",
                        provider="football-data",
                        entity_id=existing.id,
                        external_id=existing.api_id,
                    )

                    if changed:

                        updated += 1

                        print(
                            f"UPDATED -> {season.season_name}"
                        )

                    else:

                        skipped += 1

                        print(
                            f"SKIPPED -> {season.season_name}"
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

            print(
                "\n========================================"
            )
            print(
                "Incremental Season ETL Summary"
            )
            print(
                "========================================"
            )
            print(
                f"Processed : {processed}"
            )
            print(
                f"Created   : {inserted}"
            )
            print(
                f"Updated   : {updated}"
            )
            print(
                f"Skipped   : {skipped}"
            )
            print(
                f"Duration  : {duration} sec"
            )
            print(
                "========================================"
            )

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

            print(
                "\nIncremental Season ETL failed."
            )

            print(e)

            raise

        finally:

            self.db.close()


if __name__ == "__main__":

    from app.db.session import SessionLocal

    db = SessionLocal()

    try:

        IncrementalSeasonETL(db).run()

    finally:

        db.close()