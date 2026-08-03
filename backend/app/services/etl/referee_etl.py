from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.external_id import ExternalID
from app.models.match import Match
from app.models.referee import Referee
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.utils.etl_helpers import update_if_changed


class RefereeETL:
    """ETL pipeline responsible for extracting, transforming, and loading referees."""

    def __init__(self):
        self.client = FootballAPIClient()

    def extract(self, db: Session):
        """Load matches, referees and mappings required for the ETL."""
        matches = (
            db.query(Match)
            .filter(Match.referee_id.is_(None))
            .all()
        )
        referees = {
            referee.api_id: referee for referee in db.query(Referee).all()
        }
        mappings = {
            mapping.entity_id: mapping
            for mapping in db.query(ExternalID)
            .filter(ExternalID.entity_type == "referee")
            .all()
        }
        return (
            matches,
            referees,
            mappings,
        )

    def transform(self, matches, referees):
        """
        Transform API referee data into Referee objects
        and assign the main referee to each match.
        """

        transformed_referees = {}

        for match in matches:

            print(f"Fetching referees for Match {match.api_id}...")

            response = self.client.get(f"/matches/{match.api_id}")

            if not response:
                continue

            referee_list = response.get("referees", [])

            if not referee_list:
                continue

            for referee_data in referee_list:

                api_id = referee_data.get("id")

                if api_id is None:
                    continue

                referee = referees.get(api_id)

                if referee is None:

                    name = referee_data.get("name", "").strip()

                    first_name = None
                    last_name = None

                    if name:
                        parts = name.split()

                        if len(parts) > 1:
                            first_name = parts[0]
                            last_name = " ".join(parts[1:])
                        else:
                            first_name = name

                    referee = Referee(
                        api_id=api_id,
                        name=name,
                        first_name=first_name,
                        last_name=last_name,
                        nationality=referee_data.get("nationality"),
                    )

                    referees[api_id] = referee

                transformed_referees[api_id] = referee

                if referee_data.get("type") == "REFEREE":
                    match.referee = referee

        return list(transformed_referees.values())

    def load(
        self,
        db: Session,
        matches,
        referees,
        mappings,
    ):
        """
        Insert or update referees and save mappings.
        """

        inserted = 0
        updated = 0
        skipped = 0

        existing_referees = {
            referee.api_id: referee
            for referee in db.query(Referee).all()
        }

        for referee in referees:

            existing = existing_referees.get(referee.api_id)

            # ----------------------------------------
            # New Referee
            # ----------------------------------------
            if existing is None:

                db.add(referee)
                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type="referee",
                    provider="football-data",
                    entity_id=referee.id,
                    external_id=referee.api_id,
                    existing_mappings=mappings,
                )

                existing_referees[referee.api_id] = referee

                inserted += 1

            # ----------------------------------------
            # Existing Referee
            # ----------------------------------------
            else:

                changed = update_if_changed(
                    existing,
                    referee,
                    fields=[
                        "name",
                        "first_name",
                        "last_name",
                        "nationality",
                        "date_of_birth",
                        "photo",
                    ],
                )

                MappingService.save_mapping(
                    db=db,
                    entity_type="referee",
                    provider="football-data",
                    entity_id=existing.id,
                    external_id=existing.api_id,
                    existing_mappings=mappings,
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        db.commit()

        print("\nBatch committed successfully.")
        print(f"Inserted Referees : {inserted}")
        print(f"Updated Referees  : {updated}")
        print(f"Skipped Referees  : {skipped}")

    def run(self):
        """
        Execute the complete Referee ETL pipeline.
        """

        BATCH_SIZE = 100

        db = SessionLocal()

        try:

            matches, existing_referees, mappings = self.extract(db)

            total_matches = len(matches)

            print(f"\nMatches Remaining : {total_matches}")

            if total_matches == 0:
                print("All referees have already been processed.")
                return

            total_batches = (total_matches + BATCH_SIZE - 1) // BATCH_SIZE

            for batch_number, start in enumerate(
                range(0, total_matches, BATCH_SIZE),
                start=1,
            ):

                batch_matches = matches[start:start + BATCH_SIZE]

                print("\n" + "=" * 60)
                print(
                    f"Batch {batch_number}/{total_batches} "
                    f"({len(batch_matches)} matches)"
                )
                print("=" * 60)

                transformed_referees = self.transform(
                    batch_matches,
                    existing_referees,
                )

                self.load(
                    db=db,
                    matches=batch_matches,
                    referees=transformed_referees,
                    mappings=mappings,
                )

                print(
                    f"Completed Batch {batch_number}/{total_batches}"
                )

            print("\nReferee ETL Completed Successfully!")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
