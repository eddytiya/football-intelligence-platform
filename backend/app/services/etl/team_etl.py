from sqlalchemy.orm import Session

from app.constants.entities import Entities
from app.constants.providers import Providers
from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.competition_team import CompetitionTeam
from app.models.team import Team
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.utils.etl_helpers import update_if_changed
from app.models.external_id import ExternalID

class TeamETL:
    """
    ETL pipeline responsible for extracting,
    transforming, and loading teams.
    """

    def __init__(self):
        self.client = FootballAPIClient()

    def extract(self, competition_api_id):
        """
        Extract all teams for a competition.
        """

        endpoint = f"/competitions/{competition_api_id}/teams"

        return self.client.get(endpoint)

    def transform(self, data, competition_id):
        """
        Transform raw API response into Team objects.
        """

        teams = []

        if not data:
            return teams

        for team_data in data.get("teams", []):

            # -----------------------------
            # Validate required fields
            # -----------------------------
            if team_data.get("id") is None:
                print("Skipping team: Missing API ID.")
                continue

            if not team_data.get("name"):
                print(
                    f"Skipping Team {team_data.get('id')} : Missing name."
                )
                continue

            team = Team(
                api_id=team_data.get("id"),

                # Stadium ETL will populate later
                stadium_id=None,

                name=team_data.get("name"),

                short_name=team_data.get("shortName"),

                tla=team_data.get("tla"),

                crest=team_data.get("crest"),

                address=team_data.get("address"),

                website=team_data.get("website"),

                founded=team_data.get("founded"),

                club_colors=team_data.get("clubColors"),

                venue=team_data.get("venue"),

                last_updated=team_data.get("lastUpdated"),
            )

            # Temporary attribute used to create
            # CompetitionTeam relationship during load()
            team.competition_id = competition_id

            teams.append(team)

        return teams

    def load(self, db: Session, teams):
        """
        Insert new teams.
        Update changed teams.
        Create Competition-Team mappings.
        Save ExternalID mappings.
        Skip unchanged teams.
        """

        inserted = 0
        updated = 0
        skipped = 0
        mappings_created = 0

        existing_teams = {
            team.api_id: team
            for team in db.query(Team).all()
        }

        existing_mappings = {
            (
                mapping.competition_id,
                mapping.team_id,
            )
            for mapping in db.query(CompetitionTeam).all()
        }

        existing_external_ids = {
            mapping.entity_id: mapping
            for mapping in (
                db.query(ExternalID)
                .filter(
                    ExternalID.entity_type == Entities.TEAM,
                    ExternalID.provider == Providers.FOOTBALL_DATA,
                )
                .all()
            )
        }

        for team in teams:

            competition_id = team.competition_id

            existing = existing_teams.get(team.api_id)

            if existing is None:

                db.add(team)
                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type=Entities.TEAM,
                    provider=Providers.FOOTBALL_DATA,
                    entity_id=team.id,
                    external_id=team.api_id,
                    existing_mappings=existing_external_ids,
                )

                inserted += 1
                team_id = team.id

            else:

                changed = update_if_changed(
                    existing,
                    team,
                    [
                        "name",
                        "short_name",
                        "tla",
                        "crest",
                        "address",
                        "website",
                        "founded",
                        "club_colors",
                        "venue",
                        "last_updated",
                    ],
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

                MappingService.save_mapping(
                    db=db,
                    entity_type=Entities.TEAM,
                    provider=Providers.FOOTBALL_DATA,
                    entity_id=existing.id,
                    external_id=existing.api_id,
                    existing_mappings=existing_external_ids,
                )

                team_id = existing.id

            mapping_key = (
                competition_id,
                team_id,
            )

            if mapping_key not in existing_mappings:

                db.add(
                    CompetitionTeam(
                        competition_id=competition_id,
                        team_id=team_id,
                    )
                )

                existing_mappings.add(mapping_key)

                mappings_created += 1

        db.commit()

        print("\n========== Team Load Summary ==========")
        print(f"Inserted Teams      : {inserted}")
        print(f"Updated Teams       : {updated}")
        print(f"Skipped Teams       : {skipped}")
        print(f"Competition Links   : {mappings_created}")
        print("=======================================")

    def run(self):
        """
        Execute the complete Team ETL.
        """

        print("\n========== Team ETL Started ==========\n")

        db = SessionLocal()

        try:

            competitions = db.query(Competition).all()

            print(f"Found {len(competitions)} competitions.\n")

            total_processed = 0

            for competition in competitions:

                print(f"Fetching teams for {competition.name}...")

                data = self.extract(
                    competition.api_id
                )

                if not data:
                    print(
                        f"No data received for {competition.name}.\n"
                    )
                    continue

                teams = self.transform(
                    data,
                    competition.id,
                )

                self.load(
                    db,
                    teams,
                )

                total_processed += len(teams)

                print(
                    f"✓ {len(teams)} teams processed for "
                    f"{competition.name}\n"
                )

            print("=" * 50)
            print("Team ETL Completed Successfully!")
            print(f"Total Teams Processed : {total_processed}")
            print("=" * 50)

        except Exception as e:

            db.rollback()

            print(f"\nETL Failed : {e}")

            raise

        finally:

            db.close()

            print("\n✓ Database session closed.")


if __name__ == "__main__":
    TeamETL().run()