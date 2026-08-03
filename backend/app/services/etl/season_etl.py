from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.season import Season
from app.services.football_api import FootballAPIClient
from app.utils.date_parser import parse_date
from app.utils.etl_helpers import update_if_changed
from app.services.mapping_service import MappingService

class SeasonETL:
    """
    ETL pipeline responsible for extracting,
    transforming, and loading seasons.
    """

    def __init__(self):
        self.client = FootballAPIClient()

    def extract(self):
        """
        Extract season data from Football-Data.org.
        """
        return self.client.get("/competitions")

    def transform(self, data):
        """
        Transform raw API response into Season objects.
        """

        seasons = []

        if not data:
            return seasons

        for competition in data.get("competitions", []):

            current_season = competition.get("currentSeason")

            if not current_season:
                continue

            # -----------------------------
            # Validate required fields
            # -----------------------------
            if competition.get("id") is None:
                print("Skipping season: Missing Competition API ID.")
                continue

            if current_season.get("id") is None:
                print("Skipping season: Missing Season API ID.")
                continue

            start_date = parse_date(current_season.get("startDate"))
            end_date = parse_date(current_season.get("endDate"))

            if start_date and end_date:
                if start_date.year == end_date.year:
                    season_name = str(start_date.year)
                else:
                    season_name = f"{start_date.year}/{str(end_date.year)[2:]}"
            else:
                season_name = None

            season = Season(
                api_id=current_season.get("id"),

                # Resolved during load()
                competition_id=None,

                start_date=start_date,
                end_date=end_date,

                current_matchday=current_season.get("currentMatchday"),

                season_name=season_name,

                # Updated after Team ETL
                winner_team_id=None,
            )

            # Temporary attribute used during load()
            season.competition_api_id = competition.get("id")

            seasons.append(season)

        return seasons

    def load(self, db: Session, seasons):
        """
        Insert new seasons.
        Update changed seasons.
        Skip unchanged seasons.
        """

        inserted = 0
        updated = 0
        skipped = 0

        competitions = {
            competition.api_id: competition.id
            for competition in db.query(Competition).all()
        }

        existing_seasons = {
            season.api_id: season
            for season in db.query(Season).all()
        }

        for season in seasons:

            competition_id = competitions.get(
                season.competition_api_id
            )

            if competition_id is None:
                print(
                    f"Competition with API ID "
                    f"{season.competition_api_id} not found."
                )
                continue

            season.competition_id = competition_id

            existing = existing_seasons.get(season.api_id)

            if existing is None:

                db.add(season)

                # Generate season.id before saving mapping
                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type="season",
                    provider="football-data",
                    entity_id=season.id,
                    external_id=season.api_id,
                )

                inserted += 1

            else:

                changed = update_if_changed(
                    existing,
                    season,
                    [
                        "competition_id",
                        "start_date",
                        "end_date",
                        "current_matchday",
                        "season_name",
                        "winner_team_id",
                    ],
                )

                MappingService.save_mapping(
                    db=db,
                    entity_type="season",
                    provider="football-data",
                    entity_id=existing.id,
                    external_id=existing.api_id,
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        db.commit()

        print("\n========== Season Load Summary ==========")
        print(f"Inserted : {inserted}")
        print(f"Updated  : {updated}")
        print(f"Skipped  : {skipped}")
        print("=========================================")

    def run(self):
        """
        Execute the complete Season ETL.
        """

        print("\n========== Season ETL Started ==========\n")

        print("Step 1 : Extracting seasons...")

        data = self.extract()

        if not data:
            print("No season data received.")
            return

        print(f"✓ {data.get('count', 0)} competitions extracted.\n")

        print("Step 2 : Transforming seasons...")

        seasons = self.transform(data)

        print(f"✓ {len(seasons)} Season objects created.\n")

        db = SessionLocal()

        try:

            print("Step 3 : Loading seasons...")

            self.load(db, seasons)

        finally:

            db.close()

            print("\n✓ Database session closed.")

        print("\n========== Season ETL Completed ==========")


if __name__ == "__main__":
    SeasonETL().run()