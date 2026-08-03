from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.stadium import Stadium
from app.models.team import Team
from app.utils.etl_helpers import update_if_changed


class StadiumETL:
    """
    ETL pipeline responsible for extracting,
    transforming, and loading stadium data.
    """

    def __init__(self):
        pass

    def extract(self, db: Session):
        """
        Extract all teams from the database.
        """

        teams = db.query(Team).all()

        print(f"\nFound {len(teams)} teams.\n")

        return teams

    def transform(self, teams):
        """
        Convert unique team venues into
        Stadium objects.
        """

        stadiums = []

        seen = set()

        for team in teams:

            if not team.venue:
                continue

            venue = team.venue.strip()

            if not venue:
                continue

            if venue in seen:
                continue

            seen.add(venue)

            stadiums.append(
                Stadium(
                    name=venue
                )
            )

        print(
            f"Prepared {len(stadiums)} unique stadiums.\n"
        )

        return stadiums

    def load(self, db: Session, stadiums):
        """
        Insert/update stadiums and
        link teams to them.
        """

        inserted = 0
        updated = 0
        skipped = 0
        linked = 0

        # ---------------------------------
        # Preload stadiums
        # ---------------------------------

        existing_stadiums = {
            stadium.name: stadium
            for stadium in db.query(Stadium).all()
        }

        # ---------------------------------
        # Preload teams grouped by venue
        # ---------------------------------

        teams_by_venue = {}

        for team in db.query(Team).all():

            if not team.venue:
                continue

            venue = team.venue.strip()

            teams_by_venue.setdefault(
                venue,
                []
            ).append(team)

        # ---------------------------------
        # Process stadiums
        # ---------------------------------

        for stadium in stadiums:

            existing = existing_stadiums.get(
                stadium.name
            )

            if existing is None:

                db.add(stadium)
                db.flush()

                existing = stadium

                existing_stadiums[
                    stadium.name
                ] = stadium

                inserted += 1

            else:

                changed = update_if_changed(
                    existing,
                    stadium,
                    [
                        "name",
                    ],
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

            # ---------------------------------
            # Link teams to stadium
            # ---------------------------------

            for team in teams_by_venue.get(
                existing.name,
                []
            ):

                if team.stadium_id != existing.id:

                    team.stadium_id = existing.id

                    linked += 1

        db.commit()

        print("\n========== Stadium Load Summary ==========")
        print(f"Inserted Stadiums : {inserted}")
        print(f"Updated Stadiums  : {updated}")
        print(f"Skipped Stadiums  : {skipped}")
        print(f"Teams Linked      : {linked}")
        print("==========================================")

    def run(self):
        """
        Execute the complete Stadium ETL.
        """

        print("\n========== Stadium ETL Started ==========\n")

        db = SessionLocal()

        try:

            teams = self.extract(db)

            stadiums = self.transform(teams)

            self.load(
                db,
                stadiums,
            )

            print("\n========== Stadium ETL Completed ==========\n")

        except Exception as e:

            db.rollback()

            print(f"\nETL Failed : {e}")

            raise

        finally:

            db.close()

            print("✓ Database session closed.")


if __name__ == "__main__":
    StadiumETL().run()