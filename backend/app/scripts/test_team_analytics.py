from datetime import datetime

from app.db.session import SessionLocal
from app.repositories.match_repository import MatchRepository
from app.services.feature_engineering.team_analytics import TeamAnalytics


def main():

    db = SessionLocal()

    repository = MatchRepository(db)
    analytics = TeamAnalytics(repository)

    features = analytics.build_team_features(
        team_id=95,
        before_date=datetime(2025, 1, 1),
        last_n=5,
    )

    print("\n========== TEAM FEATURES ==========\n")

    for key, value in features.items():
        print(f"{key:<25}: {value}")

    db.close()


if __name__ == "__main__":
    main()