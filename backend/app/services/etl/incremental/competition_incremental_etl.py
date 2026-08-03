from sqlalchemy.orm import Session

from app.db.session import SessionLocal

from app.services.football_api import FootballAPIClient
from app.services.sync.sync_service import SyncService

from app.services.etl.competition_etl import CompetitionETL


class CompetitionIncrementalETL:
    """
    Incremental ETL pipeline for competitions.

    Responsibilities
    ----------------
    - Download latest competitions
    - Insert new competitions
    - Update changed competitions
    - Skip unchanged competitions
    - Record synchronization history
    """

    def __init__(self):
        self.client = FootballAPIClient()
        self.sync_service = SyncService()
        self.base_etl = CompetitionETL()

    def run(self):
        """
        Execute the Competition Incremental ETL.
        """

        print("\n========== Competition Incremental ETL ==========\n")

        db: Session = SessionLocal()

        try:

            print("Step 1 : Downloading competitions...")

            data = self.base_etl.extract()

            if not data:
                print("No data received.")
                return

            print("Step 2 : Transforming competitions...")

            competitions = self.base_etl.transform(data)

            print(f"{len(competitions)} competitions prepared.\n")

            print("Step 3 : Synchronizing database...")

            self.base_etl.load(
                db=db,
                competitions=competitions,
            )

            print("\nCompetition synchronization completed.")

        except Exception:

            db.rollback()
            raise

        finally:

            db.close()

            print("\nDatabase session closed.")