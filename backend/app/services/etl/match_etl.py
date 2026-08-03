from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.match import Match
from app.models.season import Season
from app.models.stadium import Stadium
from app.models.team import Team
from app.services.football_api import FootballAPIClient
from app.models.external_id import ExternalID
from app.services.mapping_service import MappingService
from app.utils.datetime_parser import parse_datetime
from app.utils.etl_helpers import update_if_changed
from app.services.matching.universal_match_service import UniversalMatchService

class MatchETL:
    """ETL pipeline responsible for extracting, transforming, and loading football matches."""

    def __init__(self):
        self.api = FootballAPIClient()

    def extract(self, db: Session):
        """Load all required lookup data. We preload everything once to eliminate unnecessary 
        database queries during the transform and load phases."""
        seasons = (
            db.query(Season)
            .filter(Season.start_date.isnot(None))
            .all()
        )
        competitions = {
            competition.id: competition for competition in db.query(Competition).all()
        }
        teams = {
            team.api_id: team for team in db.query(Team).all()
        }
        

        print("\n========== Match Extract ==========")
        print(f"Loaded Seasons        : {len(seasons)}")
        print(f"Loaded Competitions   : {len(competitions)}")
        print(f"Loaded Teams          : {len(teams)}")
        
        print("===================================\n")

        return (
            seasons,
            competitions,
            teams,
            
        )

    def transform(
        self,
        seasons,
        competitions,
        teams,
    ):
        """
        Fetch matches from Football-Data.org and transform them
        into Match model objects.
        """

        matches = []

        # Store every processed API match ID
        seen_matches = set()

        print("\n========== Match Transform ==========\n")

        for season in seasons:

            competition = competitions.get(season.competition_id)

            if not competition or not competition.code:
                print(f"Skipping Season {season.id} (Competition not found)")
                continue

            season_year = season.start_date.year

            print(f"Fetching {competition.code} {season_year}...")

            response = self.api.get(
                f"/competitions/{competition.code}/matches",
                params={"season": season_year},
            )

            if not response or "matches" not in response:
                print(f"No matches found for {competition.code} {season_year}")
                continue

            for match_data in response["matches"]:
                api_id = str(match_data["id"])

                if api_id in seen_matches:
                    continue

                seen_matches.add(api_id)

                home_team = teams.get(match_data["homeTeam"]["id"])
                away_team = teams.get(match_data["awayTeam"]["id"])

                if home_team is None or away_team is None:
                    continue

                score = match_data.get("score") or {}
                full_time = score.get("fullTime") or {}

                stadium_id = home_team.stadium_id

                match = Match(
                    api_id=api_id,
                    competition_id=competition.id,
                    season_id=season.id,
                    referee_id=None,
                    stadium_id=stadium_id,
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    utc_date=parse_datetime(
                        match_data.get("utcDate")
                    ),
                    match_date=None,
                    kick_off=None,
                    status=match_data.get("status"),
                    match_week=match_data.get("matchday"),
                    stage=match_data.get("stage"),
                    home_score=full_time.get("home") or 0,
                    away_score=full_time.get("away") or 0,
                )

                matches.append(match)

            print(f"Fetched {len(response['matches'])} matches.")

        print(f"\nTotal Matches Prepared : {len(matches)}")
        print("=====================================\n")

        return matches

    def load(
        self,
        db: Session,
        matches,
    ):
        """
        Insert new matches and update existing ones.
        """
        universal_service = UniversalMatchService(db)
        
        existing_matches = {
            match.api_id: match
            for match in db.query(Match).all()
        }

        print(f"Existing Matches Loaded : {len(existing_matches)}")
        print(f"Sample Keys : {list(existing_matches.keys())[:10]}")
        print(f"Looking for : {matches[0].api_id}")
        print(f"Exists? : {matches[0].api_id in existing_matches}")

        existing_external_ids = {
            mapping.entity_id: mapping
            for mapping in (
                db.query(ExternalID)
                .filter(
                    ExternalID.entity_type == "match",
                    ExternalID.provider == "football-data",
                )
                .all()
            )
        }

        inserted = 0
        updated = 0
        skipped = 0

        processed_api_ids = set()

        for match in matches:

            # Skip duplicate matches within this ETL run
            if match.api_id in processed_api_ids:
                skipped += 1
                continue

            processed_api_ids.add(match.api_id)

            existing = existing_matches.get(match.api_id)

            if existing is None:

                print(f"[INSERT] {match.api_id}")

                canonical_match, inserted_match = (
                    universal_service.process_match(match)
                )

                db.flush()

                MappingService.save_mapping(
                    db=db,
                    entity_type="match",
                    provider="football-data",
                    entity_id=canonical_match.id,
                    external_id=match.api_id,
                    existing_mappings=existing_external_ids,
                )

                if inserted_match:
                    existing_matches[canonical_match.api_id] = canonical_match
                    inserted += 1
                else:
                    updated += 1

            else:

                print(f"[UPDATE] {match.api_id}")

                changed = update_if_changed(
                    existing,
                    match,
                    [
                        "competition_id",
                        "season_id",
                        "referee_id",
                        "stadium_id",
                        "home_team_id",
                        "away_team_id",
                        "utc_date",
                        "match_date",
                        "kick_off",
                        "status",
                        "match_week",
                        "stage",
                        "home_score",
                        "away_score",
                    ],
                )

                MappingService.save_mapping(
                    db=db,
                    entity_type="match",
                    provider="football-data",
                    entity_id=existing.id,
                    external_id=existing.api_id,
                    existing_mappings=existing_external_ids,
                )

                if changed:
                    updated += 1
                else:
                    skipped += 1

        print("\n========== Match Load Summary ==========")
        print(f"Inserted Matches : {inserted}")
        print(f"Updated Matches  : {updated}")
        print(f"Skipped Matches  : {skipped}")
        print("========================================")

    def run(self):
        """Execute the complete Match ETL pipeline."""
        db = SessionLocal()
        try:
            seasons, competitions, teams = self.extract(db)
            matches = self.transform(
                seasons,
                competitions,
                teams,
                
            )
            self.load(db, matches)
            db.commit()
            print("\n========== Match ETL Completed ==========\n")
        except Exception as e:
            db.rollback()
            print(f"\nMatch ETL failed: {e}")
            raise
        finally:
            db.close()
            print("✓ Database session closed.")


if __name__ == "__main__":
    MatchETL().run()
