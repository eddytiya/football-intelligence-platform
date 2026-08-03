from app.db.session import SessionLocal
from app.models.competition import Competition
from etl.extract.football_data import FootballDataExtractor
from etl.utils.logger import logger


def main():
    logger.info("Starting Competition Loader...")

    db = SessionLocal()

    try:
        extractor = FootballDataExtractor()

        response = extractor.get_competitions()
        competitions = response.get("competitions", [])

        logger.info(f"Fetched {len(competitions)} competitions.")

        inserted = 0
        skipped = 0

        for comp in competitions:

            existing = (
                db.query(Competition)
                .filter(Competition.api_id == comp["id"])
                .first()
            )

            if existing:
                skipped += 1
                continue

            competition = Competition(
                api_id=comp["id"],
                name=comp["name"],
                code=comp.get("code"),
                type=comp.get("type"),
                area_name=comp["area"]["name"],
                area_code=comp["area"].get("code"),
                area_flag=comp["area"].get("flag"),
                emblem=comp.get("emblem"),
                seasons_available=comp.get("numberOfAvailableSeasons", 0),
            )

            db.add(competition)
            inserted += 1

        db.commit()

        logger.info(f"Inserted: {inserted}")
        logger.info(f"Skipped: {skipped}")

        extractor.close()

    except Exception:
        db.rollback()
        logger.exception("Error while loading competitions.")

    finally:
        db.close()
        logger.info("Database session closed.")


if __name__ == "__main__":
    main()