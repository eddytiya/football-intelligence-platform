import time
import traceback

from sqlalchemy.orm import Session

from app.models.competition import Competition
from app.models.season import Season
from app.models.standing import Standing
from app.models.team import Team
from app.repositories.standing_repository import StandingRepository
from app.repositories.sync_repository import SyncRepository
from app.services.football_api import FootballAPIClient
from app.services.sync.sync_service import SyncService
from app.utils.etl_helpers import update_if_changed


class IncrementalStandingETL:
    """
    Incremental ETL for Standings.
    Updates only changed standings.
    """

    def __init__(self, db: Session):

        self.db = db

        self.client = FootballAPIClient()

        self.sync_repository = SyncRepository(db)

        self.sync_service = SyncService(
            self.sync_repository
        )

        self.standing_repository = StandingRepository(db)

    # ==========================================================
    # Run
    # ==========================================================

    def run(self):

        print("\n========================================")
        print("Incremental Standing ETL")
        print("========================================")

        start_time = time.time()

        processed = 0
        created = 0
        updated = 0
        skipped = 0

        sync_log = None

        try:

            sync_window = self.sync_service.get_sync_window(
                provider="football-data",
                resource="standings",
            )

            sync_log = self.sync_service.create_sync_log(
                provider="football-data",
                resource="standings",
            )

            competitions = (
                self.db.query(Competition)
                .all()
            )

            teams = {
                team.api_id: team
                for team in self.db.query(Team).all()
            }

            seasons = {
                (
                    season.competition_id,
                    season.start_year,
                ): season
                for season in self.db.query(Season).all()
            }

            existing = {
                (
                    standing.competition_id,
                    standing.season_id,
                    standing.team_id,
                ): standing
                for standing in self.db.query(Standing).all()
            }

            for competition in competitions:

                print(
                    f"\nFetching standings for "
                    f"{competition.code}"
                )

                response = self.client.get(
                    f"/competitions/{competition.code}/standings"
                )

                if not response:
                    continue

                season_data = response.get(
                    "season",
                    {},
                )

                season = seasons.get(
                    (
                        competition.id,
                        season_data.get("startDate", "")[:4]
                        and int(
                            season_data["startDate"][:4]
                        ),
                    )
                )

                if season is None:
                    continue

                for standing_type in response.get(
                    "standings",
                    [],
                ):

                    table = standing_type.get(
                        "table",
                        [],
                    )

                    for row in table:

                        processed += 1

                        team = teams.get(
                            row["team"]["id"]
                        )

                        if team is None:
                            skipped += 1
                            continue

                        key = (
                            competition.id,
                            season.id,
                            team.id,
                        )

                        new_standing = Standing(
                            competition_id=competition.id,
                            season_id=season.id,
                            team_id=team.id,
                            position=row.get("position"),
                            played_games=row.get("playedGames"),
                            won=row.get("won"),
                            draw=row.get("draw"),
                            lost=row.get("lost"),
                            points=row.get("points"),
                            goals_for=row.get("goalsFor"),
                            goals_against=row.get("goalsAgainst"),
                            goal_difference=row.get(
                                "goalDifference"
                            ),
                        )

                        current = existing.get(key)

                        if current is None:

                            self.db.add(new_standing)

                            self.db.flush()

                            existing[key] = new_standing

                            created += 1

                        else:

                            changed = update_if_changed(
                                current,
                                new_standing,
                                [
                                    "position",
                                    "played_games",
                                    "won",
                                    "draw",
                                    "lost",
                                    "points",
                                    "goals_for",
                                    "goals_against",
                                    "goal_difference",
                                ],
                            )

                            if changed:
                                updated += 1
                            else:
                                skipped += 1

            self.db.commit()

            duration = round(
                time.time() - start_time,
                2,
            )

            self.sync_service.complete_sync(
                sync_log=sync_log,
                processed=processed,
                inserted=created,
                updated=updated,
                duration=duration,
            )

            print("\n========================================")
            print("Incremental Standing ETL Summary")
            print("========================================")
            print(f"Processed : {processed}")
            print(f"Created   : {created}")
            print(f"Updated   : {updated}")
            print(f"Skipped   : {skipped}")
            print(f"Duration  : {duration} sec")
            print("========================================")

        except Exception:

            self.db.rollback()

            duration = round(
                time.time() - start_time,
                2,
            )

            if sync_log:

                self.sync_service.fail_sync(
                    sync_log=sync_log,
                    duration=duration,
                )

            print("\nIncremental Standing ETL Failed\n")

            traceback.print_exc()

            raise

        