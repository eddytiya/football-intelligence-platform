from sqlalchemy.orm import Session

from app.constants.entities import Entities
from app.constants.providers import Providers
from app.db.session import SessionLocal
from app.models.competition import Competition
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.utils.etl_helpers import update_if_changed


class CompetitionETL:
    """
    ETL pipeline responsible for extracting,
    transforming, and loading football competitions.
    """

    def __init__(self):
        self.client = FootballAPIClient()

    def extract(self):
        """
        Extract competition data from Football-Data.org.
        """
        return self.client.get("/competitions")

    def transform(self, data):
        """
        Transform raw API response into Competition objects.
        """

        competitions = []

        if not data:
            return competitions

        for item in data.get("competitions", []):

            area = item.get("area") or {}

            # ----------------------------------------
            # Validate required fields
            # ----------------------------------------

            required_fields = {
                "id": item.get("id"),
                "name": item.get("name"),
                "code": item.get("code"),
                "type": item.get("type"),
                "area_name": area.get("name"),
                "area_code": area.get("code"),
            }

            missing = [
                field
                for field, value in required_fields.items()
                if value is None or (isinstance(value, str) and not value.strip())
            ]

            if missing:
                print(
                    f"Skipping competition "
                    f"{item.get('id', 'Unknown')} "
                    f"(Missing: {', '.join(missing)})"
                )
                continue

            competition = Competition(
                api_id=item.get("id"),
                name=item.get("name"),
                code=item.get("code"),
                type=item.get("type"),
                area_name=area.get("name"),
                area_code=area.get("code"),
                area_flag=area.get("flag"),
                emblem=item.get("emblem"),
                seasons_available=item.get("numberOfAvailableSeasons"),
            )

            competitions.append(competition)

        return competitions

    def load(self, db: Session, competitions):
        """
        Insert new competitions.
        Update changed competitions.
        Skip unchanged competitions.
        """

        inserted = 0
        updated = 0
        skipped = 0

        existing_competitions = {
            competition.api_id: competition
            for competition in db.query(Competition).all()
        }

        for competition in competitions:

            existing = existing_competitions.get(competition.api_id)

            if existing is None:

                db.add(competition)
                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type=Entities.COMPETITION,
                    provider=Providers.FOOTBALL_DATA,
                    entity_id=competition.id,
                    external_id=competition.api_id,
                )

                inserted += 1

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
                    db=db,
                    entity_type=Entities.COMPETITION,
                    provider=Providers.FOOTBALL_DATA,
                    entity_id=existing.id,
                    external_id=existing.api_id,
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        db.commit()

        print("\n========== Competition Load Summary ==========")
        print(f"Inserted : {inserted}")
        print(f"Updated  : {updated}")
        print(f"Skipped  : {skipped}")
        print("==============================================")

    def run(self):
        """
        Execute the complete ETL pipeline.
        """

        print("\n========== Competition ETL Started ==========\n")

        print("Step 1 : Extracting competitions...")

        data = self.extract()

        if not data:
            print("No competition data received.")
            return

        print(f"✓ {data.get('count', 0)} competitions extracted.\n")

        print("Step 2 : Transforming competitions...")

        competitions = self.transform(data)

        print(f"✓ {len(competitions)} Competition objects created.\n")

        db = SessionLocal()

        try:

            print("Step 3 : Loading competitions...")

            self.load(db, competitions)

        finally:

            db.close()

            print("\n✓ Database session closed.")

        print("\n========== Competition ETL Completed ==========")


if __name__ == "__main__":
    CompetitionETL().run()