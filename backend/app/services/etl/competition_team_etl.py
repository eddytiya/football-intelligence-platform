from sqlalchemy.orm import Session

from app.constants.entities import Entities
from app.constants.providers import Providers
from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.competition_team import CompetitionTeam
from app.models.team import Team
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService


class CompetitionTeamETL:
    """
    ETL pipeline responsible for loading
    Competition-Team relationships.
    """

    def __init__(self):
        self.client = FootballAPIClient()

    # ==========================================================
    # Extract
    # ==========================================================

    def extract(self):

        competitions = self.client.get("/competitions")

        if not competitions:
            return []

        return competitions.get("competitions", [])

    # ==========================================================
    # Transform
    # ==========================================================

    def transform(
        self,
        competition_data,
    ):

        relationships = []

        for competition in competition_data:

            competition_api_id = competition.get("id")

            if competition_api_id is None:
                continue

            print(
                f"\nFetching teams for "
                f"{competition.get('name')}"
            )

            data = self.client.get(
                f"/competitions/{competition_api_id}/teams"
            )

            if not data:
                continue

            teams = data.get("teams", [])

            for team in teams:

                team_api_id = team.get("id")

                if team_api_id is None:
                    continue

                relationships.append(
                    {
                        "competition_api_id": competition_api_id,
                        "team_api_id": team_api_id,
                    }
                )

        return relationships

    # ==========================================================
    # Load
    # ==========================================================

    def load(
        self,
        db: Session,
        relationships,
    ):

        inserted = 0
        skipped = 0

        competitions = {

            competition.api_id: competition.id

            for competition in db.query(
                Competition
            ).all()

        }

        teams = {

            team.api_id: team.id

            for team in db.query(
                Team
            ).all()

        }

        existing = {

            (
                item.competition_id,
                item.team_id,
            )

            for item in db.query(
                CompetitionTeam
            ).all()

        }

        for relation in relationships:

            competition_id = competitions.get(
                relation["competition_api_id"]
            )

            team_id = teams.get(
                relation["team_api_id"]
            )

            if competition_id is None:

                print(
                    f"Competition not found "
                    f"{relation['competition_api_id']}"
                )

                continue

            if team_id is None:

                print(
                    f"Team not found "
                    f"{relation['team_api_id']}"
                )

                continue

            key = (
                competition_id,
                team_id,
            )

            if key in existing:

                skipped += 1

                continue

            competition_team = CompetitionTeam(

                competition_id=competition_id,

                team_id=team_id,
            )

            db.add(
                competition_team
            )

            db.flush()

            MappingService.save_mapping(

                db=db,

                entity_type=Entities.COMPETITION_TEAM,

                provider=Providers.FOOTBALL_DATA,

                entity_id=competition_team.id,

                external_id=(
                    f"{competition_id}_{team_id}"
                ),
            )

            existing.add(key)

            inserted += 1
            db.commit()

        print("\n========== Competition Team Load Summary ==========")
        print(f"Inserted : {inserted}")
        print(f"Skipped  : {skipped}")
        print("===================================================")

    # ==========================================================
    # Run
    # ==========================================================

    def run(self):

        print(
            "\n========== Competition Team ETL Started ==========\n"
        )

        print("Step 1 : Extracting competitions...")

        competition_data = self.extract()

        if not competition_data:

            print("No competitions found.")

            return

        print(
            f"✓ {len(competition_data)} competitions extracted.\n"
        )

        print(
            "Step 2 : Fetching competition teams..."
        )

        relationships = self.transform(
            competition_data
        )

        print(
            f"✓ {len(relationships)} relationships created.\n"
        )

        db = SessionLocal()

        try:

            print(
                "Step 3 : Loading Competition-Team relationships..."
            )

            self.load(
                db=db,
                relationships=relationships,
            )

        finally:

            db.close()

            print(
                "\n✓ Database session closed."
            )

        print(
            "\n========== Competition Team ETL Completed =========="
        )


if __name__ == "__main__":

    CompetitionTeamETL().run()