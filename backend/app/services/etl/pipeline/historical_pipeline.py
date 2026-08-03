from app.services.etl.coach_etl import CoachETL
from app.services.etl.competition_etl import CompetitionETL
from app.services.etl.match_etl import MatchETL
from app.services.etl.player_etl import PlayerETL
from app.services.etl.referee_etl import RefereeETL
from app.services.etl.season_etl import SeasonETL
from app.services.etl.stadium_etl import StadiumETL
from app.services.etl.standing_etl import StandingETL
from app.services.etl.team_etl import TeamETL


class HistoricalPipeline:
    """
    Master ETL pipeline.

    Executes every ETL in the correct order so that
    dependencies are satisfied.
    """

    def __init__(self):
        self.competition_etl = CompetitionETL()
        self.season_etl = SeasonETL()
        self.team_etl = TeamETL()
        self.stadium_etl = StadiumETL()
        self.coach_etl = CoachETL()
        self.player_etl = PlayerETL()
        self.match_etl = MatchETL()
        self.referee_etl = RefereeETL()
        self.standing_etl = StandingETL()

    def run(self):
        """
        Execute the complete historical ETL pipeline.
        """

        print("=" * 70)
        print("Football Intelligence Platform")
        print("Historical ETL Pipeline")
        print("=" * 70)

        steps = [
            ("Competitions", self.competition_etl),
            ("Seasons", self.season_etl),
            ("Teams", self.team_etl),
            ("Stadiums", self.stadium_etl),
            ("Coaches", self.coach_etl),
            ("Players", self.player_etl),
            ("Matches", self.match_etl),
            ("Referees", self.referee_etl),
            ("Standings", self.standing_etl),
        ]

        for name, etl in steps:
            print(f"\n{name}")
            print("-" * 70)
            etl.run()

        print("\n" + "=" * 70)
        print("Historical ETL Completed Successfully")
        print("=" * 70)


if __name__ == "__main__":
    HistoricalPipeline().run()