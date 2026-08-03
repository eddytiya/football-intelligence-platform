from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.team import Team

from etl.extract.football_data import FootballDataExtractor
from etl.utils.logger import logger


def main():
    logger.info("Starting Team Loader...")

    db = SessionLocal()

    try:
        extractor = FootballDataExtractor()

        # Fetch all competitions from the database
        competitions = db.query(Competition).all()

        logger.info(f"Found {len(competitions)} competitions.")

        total_inserted = 0
        total_skipped = 0

        # Loop through every competition
        for competition in competitions:

            logger.info(
                f"Loading teams for {competition.name} ({competition.code})"
            )

            # Fetch teams from Football Data API
            response = extractor.get_teams(competition.code)

            teams = response.get("teams", [])

            inserted = 0
            skipped = 0

            # Loop through all teams
            for team in teams:

                # Check if the team already exists
                existing_team = (
                    db.query(Team)
                    .filter(Team.api_id == team["id"])
                    .first()
                )

                if existing_team:
                    skipped += 1
                    continue

                # Create Team object
                new_team = Team(
                    api_id=team["id"],
                    competition_id=competition.id,
                    name=team["name"],
                    short_name=team.get("shortName"),
                    tla=team.get("tla"),
                    crest=team.get("crest"),
                    address=team.get("address"),
                    website=team.get("website"),
                    founded=team.get("founded"),
                    club_colors=team.get("clubColors"),
                    venue=team.get("venue"),
                    last_updated=team.get("lastUpdated"),
                )

                db.add(new_team)

                inserted += 1

            db.commit()

            total_inserted += inserted
            total_skipped += skipped

            logger.info(
                f"{competition.name}: Inserted {inserted}, Skipped {skipped}"
            )

        extractor.close()

        logger.info("===================================")
        logger.info(f"Total Inserted : {total_inserted}")
        logger.info(f"Total Skipped  : {total_skipped}")
        logger.info("Team loading completed successfully.")
        logger.info("===================================")

    except Exception:
        db.rollback()
        logger.exception("Team Loader Failed.")

    finally:
        db.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    main()