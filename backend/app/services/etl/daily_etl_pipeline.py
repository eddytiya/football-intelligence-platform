import traceback
import time

from app.services.etl.incremental_competition_etl import IncrementalCompetitionETL
from app.services.etl.incremental_season_etl import IncrementalSeasonETL
from app.services.etl.incremental_team_etl import IncrementalTeamETL
from app.services.etl.stadium_etl import StadiumETL
from app.services.etl.incremental_standing_etl import IncrementalStandingETL
from app.services.etl.incremental_match_etl import IncrementalMatchETL
from app.services.etl.referee_etl import RefereeETL


class DailyETLPipeline:
    """
    Runs the complete daily ETL pipeline.
    """

    def __init__(self, db):
        self.db = db

    def run(self):

        start = time.time()

        print("\n" + "=" * 60)
        print("Daily Football ETL Pipeline")
        print("=" * 60)

        try:

            print("\n[1/7] Competition ETL")
            IncrementalCompetitionETL(self.db).run()

            print("\n[2/7] Season ETL")
            IncrementalSeasonETL(self.db).run()

            print("\n[3/7] Team ETL")
            IncrementalTeamETL(self.db).run()

            print("\n[4/7] Stadium ETL")
            StadiumETL().run()

            print("\n[5/7] Standing ETL")
            IncrementalStandingETL(self.db).run()

            print("\n[6/7] Match ETL")
            IncrementalMatchETL(self.db).run()

            print("\n[7/7] Referee ETL")
            RefereeETL().run()

            duration = time.time() - start

            print("\n" + "=" * 60)
            print("Daily ETL Pipeline Completed Successfully")
            print("=" * 60)
            print(f"Duration : {duration:.2f} seconds")

        except Exception:

            traceback.print_exc()
            raise