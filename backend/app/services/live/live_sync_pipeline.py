import time
import traceback

from sqlalchemy.orm import Session

from app.services.etl.incremental_match_etl import IncrementalMatchETL
from app.services.etl.incremental_standing_etl import IncrementalStandingETL
from app.services.etl.referee_etl import RefereeETL
from app.services.live.match_checker import MatchChecker


class LiveSyncPipeline:
    """
    Runs the lightweight live synchronization pipeline.
    """

    def __init__(self, db: Session):

        self.db = db

    def run(self):

        print("\n" + "=" * 60)
        print("Live Sync Pipeline")
        print("=" * 60)

        start = time.time()

        try:

            # ---------------------------------------
            # Check whether sync is required
            # ---------------------------------------

            checker = MatchChecker()

            if not checker.should_sync():

                print("\nNo matches require synchronization.")
                print("Skipping Live Sync Pipeline.")

                return

            # ---------------------------------------
            # Run Incremental Match ETL
            # ---------------------------------------

            print("\n[1/3] Incremental Match ETL")

            IncrementalMatchETL(self.db).run()

            # ---------------------------------------
            # Run Incremental Standing ETL
            # ---------------------------------------

            print("\n[2/3] Incremental Standing ETL")

            IncrementalStandingETL(self.db).run()

            # ---------------------------------------
            # Run Referee ETL
            # ---------------------------------------

            print("\n[3/3] Referee ETL")

            RefereeETL().run()

            duration = time.time() - start

            print("\n" + "=" * 60)
            print("Live Sync Pipeline Completed Successfully")
            print("=" * 60)
            print(f"Duration : {duration:.2f} seconds")

        except Exception:

            traceback.print_exc()

            raise