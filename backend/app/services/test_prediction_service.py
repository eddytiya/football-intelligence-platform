from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.match_repository import MatchRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.feature_engineering.team_analytics import TeamAnalytics
from app.services.prediction_service import PredictionService


def main():

    db: Session = SessionLocal()

    try:

        match_repository = MatchRepository(db)

        prediction_repository = PredictionRepository(db)

        analytics = TeamAnalytics(
            match_repository
        )

        prediction_service = PredictionService(
            prediction_repository=prediction_repository,
            match_repository=match_repository,
            team_analytics=analytics,
        )

        next_match = (
            match_repository.get_next_match()
        )

        if next_match is None:

            print("No upcoming matches found.")
            return

        print()

        print("=" * 70)
        print("NEXT MATCH")
        print("=" * 70)

        print(
            f"Match ID : {next_match.id}"
        )

        print(
            f"{next_match.home_team.name} vs {next_match.away_team.name}"
        )

        print()

        prediction = prediction_service.predict_match(
            match_id=next_match.id,
        )

        print()

        print("=" * 70)
        print("PREDICTION")
        print("=" * 70)

        for key, value in prediction.items():

            print(f"{key}: {value}")

    finally:

        db.close()


if __name__ == "__main__":
    main()