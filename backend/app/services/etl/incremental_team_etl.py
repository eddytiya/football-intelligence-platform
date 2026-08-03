import time
import traceback

from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.competition_team import CompetitionTeam
from app.models.team import Team
from app.repositories.sync_repository import SyncRepository
from app.repositories.team_repository import TeamRepository
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.services.sync.sync_service import SyncService
from app.utils.etl_helpers import update_if_changed


class IncrementalTeamETL:
    """
    Incremental ETL pipeline for football teams.
    """

    def __init__(self, db: Session):
        self.db = db

        self.api_client = FootballAPIClient()

        self.team_repository = TeamRepository(db)

        self.sync_repository = SyncRepository(db)

        self.sync_service = SyncService(
            self.sync_repository
        )

    def run(self):
        """
        Execute an incremental synchronization.
        """

        processed = 0
        created = 0
        updated = 0
        skipped = 0

        start_time = time.perf_counter()

        start, end = self.sync_service.get_sync_window(
            provider="football-data",
            resource="teams",
        )

        print("=" * 60)
        print("Incremental Team ETL")
        print("=" * 60)
        print(f"Sync Start : {start}")
        print(f"Sync End   : {end}")

        sync_log = self.sync_service.create_sync_log(
            provider="football-data",
            resource="teams",
        )

        try:

            competitions = (
                self.db.query(Competition)
                .order_by(Competition.name.asc())
                .all()
            )

            for competition in competitions:

                print()
                print("-" * 60)
                print(f"Competition : {competition.name}")
                print("-" * 60)

                data = self.api_client.get(
                    f"/competitions/{competition.code}/teams"
                )

                if data is None:
                    continue

                teams = data.get("teams", [])

                print(f"Downloaded {len(teams)} teams.")

                for team_data in teams:

                    try:

                        api_id = str(team_data["id"])

                        existing = self.team_repository.get_team_by_api_id(
                            api_id
                        )

                        if existing:

                            print(f"UPDATE -> {existing.name}")

                            updated_team = Team(
                                api_id=existing.api_id,
                                stadium_id=existing.stadium_id,
                                name=team_data.get("name"),
                                short_name=team_data.get("shortName"),
                                tla=team_data.get("tla"),
                                crest=team_data.get("crest"),
                                address=team_data.get("address"),
                                website=team_data.get("website"),
                                founded=team_data.get("founded"),
                                club_colors=team_data.get("clubColors"),
                                venue=team_data.get("venue"),
                            )

                            update_if_changed(
                                existing=existing,
                                new_data=updated_team,
                                fields=[
                                    "name",
                                    "short_name",
                                    "tla",
                                    "crest",
                                    "address",
                                    "website",
                                    "founded",
                                    "club_colors",
                                    "venue",
                                ],
                            )

                            self.db.commit()
                            self.db.refresh(existing)

                            team = existing
                            updated += 1

                            self.db.commit()
                            self.db.refresh(existing)

                            team = existing

                            updated += 1

                        else:

                            print(f"CREATE -> {team_data.get('name')}")

                            team = Team(
                                api_id=api_id,
                                name=team_data.get("name"),
                                short_name=team_data.get("shortName"),
                                tla=team_data.get("tla"),
                                crest=team_data.get("crest"),
                            )

                            self.db.add(team)
                            self.db.commit()
                            self.db.refresh(team)

                            created += 1

                        MappingService.save_mapping(
                            db=self.db,
                            entity_type="team",
                            provider="football-data",
                            entity_id=team.id,
                            external_id=api_id,
                        )

                        self.db.commit()

                        relation = (
                            self.db.query(CompetitionTeam)
                            .filter(
                                CompetitionTeam.team_id == team.id,
                                CompetitionTeam.competition_id == competition.id,
                            )
                            .first()
                        )

                        if relation is None:

                            self.db.add(
                                CompetitionTeam(
                                    competition_id=competition.id,
                                    team_id=team.id,
                                )
                            )

                            self.db.commit()

                        processed += 1

                    except Exception as e:

                        self.db.rollback()

                        skipped += 1

                        print()
                        print("=" * 80)
                        print(f"FAILED TEAM : {team_data.get('id')}")
                        print(e)
                        traceback.print_exc()
                        print("=" * 80)

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
        print("Incremental Team ETL Summary")
        print("=" * 60)
        print(f"Processed : {processed}")
        print(f"Created   : {created}")
        print(f"Updated   : {updated}")
        print(f"Skipped   : {skipped}")
        print(f"Duration  : {duration:.2f} seconds")
        print("=" * 60)