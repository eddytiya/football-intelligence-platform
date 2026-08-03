from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.coach import Coach
from app.models.team import Team
from app.services.football_api import FootballAPIClient
from app.utils.date_parser import parse_date
from app.utils.datetime_parser import parse_datetime
from app.utils.etl_helpers import update_if_changed

class CoachETL:

    def __init__(self):
        self.api = FootballAPIClient()

    def extract(self, db: Session):
        """
        Extract all teams from the database.
        Each team will be used to fetch its
        coach details from the Football API.
        """

        teams = (
            db.query(Team)
            .filter(Team.api_id.isnot(None))
            .all()
        )

        print(f"\nFound {len(teams)} teams.\n")

        return teams

    def transform(self, teams):
        """
        Fetch coach information for each team
        from the Football API and convert it
        into Coach objects.
        """

        coaches = []

        for team in teams:

            print(f"Fetching coach for {team.name}...")

            try:
                team_data = self.api.get(f"/teams/{team.api_id}")

            except Exception as e:
                print(f"Failed to fetch {team.name}: {e}")
                continue

            if not team_data:
                continue

            coach_data = team_data.get("coach")

            if not coach_data:

                coach = Coach(
                    api_id=-(team.api_id),
                    team_id=team.id,
                    name=f"Unknown Coach ({team.name})",
                    first_name="Unknown",
                    last_name="",
                    date_of_birth=None,
                    nationality="Unknown",
                    contract_start=None,
                    contract_end=None,
                    photo="N/A",
                    last_updated=parse_datetime(team_data.get("lastUpdated"))
                )

                coaches.append(coach)
                continue

            # -------------------------------------------------
            # Create safe placeholder values for missing data
            # -------------------------------------------------

            contract = coach_data.get("contract") or {}

            coach = Coach(
                api_id=coach_data.get("id") or -(team.api_id),
                team_id=team.id,
                name=(coach_data.get("name") or f"Unknown Coach ({team.name})").strip(),
                first_name=coach_data.get("firstName") or "Unknown",
                last_name=coach_data.get("lastName") or "",
                date_of_birth=parse_date(coach_data.get("dateOfBirth")),
                nationality=coach_data.get("nationality") or "Unknown",
                contract_start=parse_date(contract.get("start")),
                contract_end=parse_date(contract.get("until")),
                photo=coach_data.get("photo") or "N/A",
                last_updated=parse_datetime(team_data.get("lastUpdated"))
            )

            coaches.append(coach)

        print(f"\nPrepared {len(coaches)} coaches.\n")

        return coaches

    def load(self, db: Session, coaches):
        """
        Insert/update coaches in the database.
        """

        inserted = 0
        updated = 0
        skipped = 0

        existing_coaches = {
            coach.api_id: coach
            for coach in db.query(Coach).all()
        }

        for coach in coaches:

            existing = existing_coaches.get(coach.api_id)

            if existing is None:

                db.add(coach)

                existing_coaches[coach.api_id] = coach

                inserted += 1

            else:

                changed = update_if_changed(
                    existing,
                    coach,
                    [
                        "team_id",
                        "name",
                        "first_name",
                        "last_name",
                        "date_of_birth",
                        "nationality",
                        "contract_start",
                        "contract_end",
                        "photo",
                        "last_updated",
                    ],
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        db.commit()

        print("\n========== Coach Load Summary ==========")
        print(f"Inserted Coaches : {inserted}")
        print(f"Updated Coaches  : {updated}")
        print(f"Skipped Coaches  : {skipped}")
        print("========================================")
        
    def run(self):
        """
        Execute the complete Coach ETL.
        """

        print("\n========== Coach ETL Started ==========\n")

        db = SessionLocal()

        try:

            teams = self.extract(db)

            coaches = self.transform(teams)

            self.load(
                db,
                coaches,
            )

            print("\n========== Coach ETL Completed ==========\n")

        except Exception as e:

            db.rollback()

            print(f"\nETL Failed : {e}")

            raise

        finally:

            db.close()

            print("✓ Database session closed.")

if __name__ == "__main__":
    CoachETL().run()