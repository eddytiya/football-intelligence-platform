from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.external_id import ExternalID
from app.models.player import Player
from app.models.team import Team
from app.services.football_api import FootballAPIClient
from app.services.mapping_service import MappingService
from app.utils.date_parser import parse_date
from app.utils.datetime_parser import parse_datetime
from app.utils.etl_helpers import update_if_changed


class PlayerETL:
    """
    ETL pipeline responsible for extracting, transforming, and loading players.
    """

    def __init__(self):
        self.api = FootballAPIClient()

    def extract(self, db: Session):
        """
        Extract all teams that have a Football-Data API ID.
        Each team will be used to fetch its squad.
        """
        teams = (
            db.query(Team)
            .filter(Team.api_id.isnot(None))
            .order_by(Team.id)
            .all()
        )
        print(f"\nFound {len(teams)} teams.\n")
        return teams

    def transform(self, teams):
        """
        Fetch every team's squad from Football-Data.org and convert each player
        into Player objects. Duplicate players are removed using their API ID.
        """

        players = {}

        for team in teams:

            print(f"Fetching squad for {team.name}...")

            try:
                team_data = self.api.get(f"/teams/{team.api_id}")
            except Exception as e:
                print(f"Failed to fetch squad for {team.name}: {e}")
                continue

            if not team_data:
                continue

            squad = team_data.get("squad", [])

            if not squad:
                print(f"No squad returned for {team.name}.")
                continue

            for player_data in squad:

                api_id = player_data.get("id")

                if api_id is None:
                    continue

                players[api_id] = Player(
                    api_id=api_id,
                    team_id=team.id,
                    name=(player_data.get("name") or "Unknown Player").strip(),
                    first_name=player_data.get("firstName"),
                    last_name=player_data.get("lastName"),
                    date_of_birth=parse_date(player_data.get("dateOfBirth")),
                    nationality=player_data.get("nationality"),
                    position=player_data.get("position"),
                    shirt_number=player_data.get("shirtNumber"),
                    last_updated=parse_datetime(team_data.get("lastUpdated")),
                )

        print(f"\nPrepared {len(players)} unique players.\n")

        return list(players.values())

    def load(self, db: Session, players):
        """
        Insert/update players and maintain ExternalID mappings.
        This method is fully optimized by:
        - Loading existing players once
        - Loading existing mappings once
        - Using O(1) dictionary lookups
        - Performing a single commit in run()
        """
        inserted = 0
        updated = 0
        skipped = 0

        # --------------------------------------------------
        # Load existing players
        # --------------------------------------------------
        existing_players = {
            player.api_id: player for player in db.query(Player).all()
        }

        # --------------------------------------------------
        # Load existing ExternalID mappings
        # --------------------------------------------------
        existing_external_ids = {
            mapping.entity_id: mapping
            for mapping in (
                db.query(ExternalID)
                .filter(
                    ExternalID.entity_type == "player",
                    ExternalID.provider == "football-data",
                )
                .all()
            )
        }

        # --------------------------------------------------
        # Insert / Update Players
        # --------------------------------------------------
        for player in players:
            existing = existing_players.get(player.api_id)

            # ----------------------------------------------
            # New Player
            # ----------------------------------------------
            if existing is None:
                db.add(player)  # Needed so player.id is generated
                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type="player",
                    provider="football-data",
                    entity_id=player.id,
                    external_id=player.api_id,
                    existing_mappings=existing_external_ids,
                )
                existing_players[player.api_id] = player
                inserted += 1

            # ----------------------------------------------
            # Existing Player
            # ----------------------------------------------
            else:
                changed = update_if_changed(
                    existing,
                    player,
                    [
                        "team_id",
                        "name",
                        "first_name",
                        "last_name",
                        "date_of_birth",
                        "nationality",
                        "position",
                        "shirt_number",
                        "last_updated",
                    ],
                )

                MappingService.save_mapping(
                    db=db,
                    entity_type="player",
                    provider="football-data",
                    entity_id=existing.id,
                    external_id=existing.api_id,
                    existing_mappings=existing_external_ids,
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        print("\n========== Player Load Summary ==========")
        print(f"Inserted Players : {inserted}")
        print(f"Updated Players : {updated}")
        print(f"Skipped Players : {skipped}")
        print("=========================================")

    def run(self):
        """
        Execute the complete Player ETL.
        """
        print("\n========== Player ETL Started ==========\n")
        db = SessionLocal()
        try:
            teams = self.extract(db)
            players = self.transform(teams)
            self.load(
                db=db,
                players=players,
            )
            db.commit()
            print("\n========== Player ETL Completed ==========\n")
        except Exception as e:
            db.rollback()
            print(f"\nETL Failed : {e}")
            raise
        finally:
            db.close()
            print("✓ Database session closed.")


if __name__ == "__main__":
    PlayerETL().run()