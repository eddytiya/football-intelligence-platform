from loguru import logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.standing import Standing
from app.models.team import Team
from etl.extract.football_data import FootballDataExtractor


def main():
    logger.info("Starting Standing Loader...")

    db: Session = SessionLocal()
    extractor = FootballDataExtractor()

    total_inserted = 0
    total_skipped = 0

    try:
        competitions = db.query(Competition).all()

        logger.info(f"Found {len(competitions)} competitions.")

        for competition in competitions:

            try:
                logger.info(
                    f"Loading standings for {competition.name} ({competition.code})"
                )

                response = extractor.get_standings(
                    competition.code
                )

                standings = response.get("standings", [])

                inserted = 0
                skipped = 0

                for table in standings:

                    if table.get("type") != "TOTAL":
                        continue

                    for row in table.get("table", []):

                        team_api_id = row["team"]["id"]

                        team = (
                            db.query(Team)
                            .filter(
                                Team.api_id == team_api_id
                            )
                            .first()
                        )

                        if not team:
                            logger.warning(
                                f"Skipping Team {team_api_id}"
                            )
                            skipped += 1
                            continue

                        existing = (
                            db.query(Standing)
                            .filter(
                                Standing.competition_id == competition.id,
                                Standing.team_id == team.id,
                            )
                            .first()
                        )

                        if existing:
                            skipped += 1
                            continue

                        standing = Standing(
                            competition_id=competition.id,
                            team_id=team.id,
                            position=row["position"],
                            played_games=row["playedGames"],
                            won=row["won"],
                            draw=row["draw"],
                            lost=row["lost"],
                            points=row["points"],
                            goals_for=row["goalsFor"],
                            goals_against=row["goalsAgainst"],
                            goal_difference=row["goalDifference"],
                        )

                        db.add(standing)
                        inserted += 1

                db.commit()

                logger.info(
                    f"{competition.name}: "
                    f"Inserted {inserted}, "
                    f"Skipped {skipped}"
                )

                total_inserted += inserted
                total_skipped += skipped

            except Exception as e:
                db.rollback()

                logger.error(
                    f"Failed loading standings for "
                    f"{competition.name}: {e}"
                )

                continue

        logger.success(
            f"Finished! "
            f"Inserted={total_inserted}, "
            f"Skipped={total_skipped}"
        )

    except Exception:
        db.rollback()
        logger.exception("Standing Loader Failed.")

    finally:
        extractor.close()
        db.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    main()