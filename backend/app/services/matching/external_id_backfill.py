from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.external_id import ExternalID


class ExternalIDBackfill:
    """
    Creates missing ExternalID mappings for existing matches.

    This is a one-time migration utility that ensures every match
    has a corresponding ExternalID record.

    Responsibilities
    ----------------
    - Scan all matches.
    - Skip matches without an api_id.
    - Skip matches that already have a mapping.
    - Create missing mappings.
    """

    PROVIDER = "football-data"

    def __init__(self, db: Session):
        self.db = db

    def run(self):
        matches_checked = 0
        mappings_added = 0
        already_exists = 0
        skipped = 0

        print("\n========== External ID Backfill ==========\n")

        matches = self.db.query(Match).all()

        for match in matches:

            matches_checked += 1

            # Skip matches without an external API ID
            if not match.api_id:
                skipped += 1
                continue

            existing_mapping = (
                self.db.query(ExternalID)
                .filter(
                    ExternalID.provider == self.PROVIDER,
                    ExternalID.external_id == str(match.api_id),
                    ExternalID.entity_type == "match",
                )
                .first()
            )

            if existing_mapping:
                already_exists += 1
                continue

            mapping = ExternalID(
                provider=self.PROVIDER,
                entity_type="match",
                entity_id=match.id,
                external_id=str(match.api_id),
            )

            self.db.add(mapping)
            mappings_added += 1

            # Commit every 500 records
            if mappings_added % 500 == 0:
                self.db.commit()

        self.db.commit()

        print("========== Backfill Summary ==========")
        print(f"Matches Checked : {matches_checked}")
        print(f"Mappings Added  : {mappings_added}")
        print(f"Already Exists  : {already_exists}")
        print(f"Skipped         : {skipped}")
        print("======================================\n")