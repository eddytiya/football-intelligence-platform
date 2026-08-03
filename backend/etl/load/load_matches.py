from datetime import datetime

from loguru import logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.competition import Competition
from app.models.match import Match
from app.models.team import Team
from etl.extract.football_data import FootballDataExtractor


class MatchLoader:
    """
    Loads football matches into the database.
    """

    def __init__(self):
        self.db: Session = SessionLocal()
        self.extractor = FootballDataExtractor()

    def load_matches(
        self,
        season: int | None = None,
    ):
        logger.info("Starting Match Loader...")

        total_inserted = 0
        total_skipped = 0

        try:
            competitions = self.db.query(Competition).all()

            logger.info(f"Found {len(competitions)} competitions.")

            for competition in competitions:

                try:
                    if season is None:
                        logger.info(
                            f"Loading matches for "
                            f"{competition.name} ({competition.code})"
                        )
                    else:
                        logger.info(
                            f"Loading {season} matches for "
                            f"{competition.name} ({competition.code})"
                        )

                    response = self.extractor.get_matches(
                        competition.code,
                        season=season,
                    )

                    matches = response.get("matches", [])

                    inserted = 0
                    skipped = 0

                    for match in matches:

                        existing_match = (
                            self.db.query(Match)
                            .filter(
                                Match.api_id == match["id"]
                            )
                            .first()
                        )

                        if existing_match:
                            skipped += 1
                            continue

                        home_team_api_id = (
                            match["homeTeam"].get("id")
                        )

                        away_team_api_id = (
                            match["awayTeam"].get("id")
                        )

                        if (
                            home_team_api_id is None
                            or away_team_api_id is None
                        ):
                            logger.warning(
                                f"Skipping Match {match['id']} "
                                f"(Missing Team API ID)"
                            )
                            skipped += 1
                            continue

                        home_team = (
                            self.db.query(Team)
                            .filter(
                                Team.api_id == home_team_api_id
                            )
                            .first()
                        )

                        away_team = (
                            self.db.query(Team)
                            .filter(
                                Team.api_id == away_team_api_id
                            )
                            .first()
                        )

                        if not home_team or not away_team:
                            logger.warning(
                                f"Skipping Match {match['id']} "
                                f"(Team not found in database)"
                            )
                            skipped += 1
                            continue

                        score = match.get("score", {})
                        full_time = score.get("fullTime", {})

                        new_match = Match(
                            api_id=match["id"],
                            competition_id=competition.id,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            utc_date=datetime.fromisoformat(
                                match["utcDate"].replace(
                                    "Z",
                                    "+00:00",
                                )
                            ),
                            status=match.get("status"),
                            matchday=match.get("matchday"),
                            stage=match.get("stage"),
                            winner=score.get("winner"),
                            home_score=full_time.get("home"),
                            away_score=full_time.get("away"),
                        )

                        self.db.add(new_match)
                        inserted += 1

                    self.db.commit()

                    logger.info(
                        f"{competition.name}: "
                        f"Inserted {inserted}, "
                        f"Skipped {skipped}"
                    )

                    total_inserted += inserted
                    total_skipped += skipped

                except Exception as e:
                    self.db.rollback()

                    logger.error(
                        f"Failed to load matches for "
                        f"{competition.name}: {e}"
                    )

                    continue

            logger.success(
                f"Finished! "
                f"Inserted={total_inserted}, "
                f"Skipped={total_skipped}"
            )

        except Exception:
            self.db.rollback()
            logger.exception("Match Loader Failed.")

    def close(self):
        self.extractor.close()
        self.db.close()
        logger.info("Database session closed.")


def main():
    loader = MatchLoader()

    try:
        loader.load_matches()

    finally:
        loader.close()


if __name__ == "__main__":
    main()