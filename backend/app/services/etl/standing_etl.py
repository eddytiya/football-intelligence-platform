from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.season import Season
from app.models.team import Team
from app.models.standing import Standing

from app.services.football_api import FootballAPIClient

from app.utils.etl_helpers import update_if_changed


class StandingETL:
    """ETL pipeline responsible for extracting, transforming, and loading league standings."""

    def __init__(self):
        self.client = FootballAPIClient()

    def extract(self, db: Session):
        """Extract all seasons, competitions, teams, existing standings, and mappings."""
        seasons = db.query(Season).all()
        
        competitions = {
            competition.id: competition 
            for competition in db.query(Competition).all()
        }
        
        teams = {
            team.api_id: team 
            for team in db.query(Team).all()
        }
        
        existing_standings = {
            (standing.competition_id, standing.season_id, standing.team_id): standing 
            for standing in db.query(Standing).all()
        }
        
        

        return (
            seasons,
            competitions,
            teams,
            existing_standings,
            
        )

    def transform(self, seasons, competitions, teams):
        """
        Transform API standings into Standing objects.
        """

        standings = []

        for season in seasons:

            competition = competitions.get(
                season.competition_id
            )

            if competition is None:
                continue

            if season.start_date is None:
                continue

            print(
                f"Fetching standings for "
                f"{competition.code} "
                f"({season.season_name})..."
            )

            response = self.client.get(
                f"/competitions/{competition.code}/standings",
                params={
                    "season": season.start_date.year,
                },
            )

            if not response:
                continue

            if not response.get("standings"):
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

                    team_data = row.get(
                        "team",
                        {},
                    )

                    team = teams.get(
                        team_data.get("id")
                    )

                    if team is None:
                        continue

                    standings.append(
                        Standing(
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
                    )

        return standings

    def load(self, db: Session, standings, existing_standings):
        """Load standings into the database."""
        inserted = 0
        updated = 0
        skipped = 0

        for standing in standings:
            key = (
                standing.competition_id,
                standing.season_id,
                standing.team_id,
            )
            existing = existing_standings.get(key)
            
            if existing is None:
                db.add(standing)
                db.flush()

                existing_standings[key] = standing

                inserted += 1
            else:
                changed = update_if_changed(
                    existing,
                    standing,
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

        print("\n========== Standing Load Summary ==========")
        print(f"Inserted Standings : {inserted}")
        print(f"Updated Standings  : {updated}")
        print(f"Skipped Standings  : {skipped}")
        print("===========================================")

    def run(self):
        """
        Run the complete Standing ETL pipeline.
        """

        db = SessionLocal()

        print("\n========== Starting Standing ETL ==========")

        try:

            (
                seasons,
                competitions,
                teams,
                existing_standings,
            ) = self.extract(db)

            standings = self.transform(
                seasons,
                competitions,
                teams,
            )

            self.load(
                db,
                standings,
                existing_standings,
            )

            db.commit()

            print("\n========== Standing ETL Completed ==========\n")

        except Exception as e:

            db.rollback()

            print(f"\nStanding ETL failed: {e}")

            raise

        finally:

            db.close()

            print("✓ Database session closed.")
