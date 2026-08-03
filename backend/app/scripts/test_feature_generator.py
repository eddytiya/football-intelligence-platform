from app.db.session import SessionLocal
from app.models.match import Match
from app.services.feature_engineering.dataset_builder import DatasetBuilder
from app.services.feature_engineering.feature_generator import FeatureGenerator
from app.services.feature_engineering.team_analytics import TeamAnalytics


def main():

    db = SessionLocal()

    try:
        builder = DatasetBuilder()

        matches_df = builder.load_finished_matches()

        first_match_id = int(matches_df.iloc[0]["match_id"])

        first_match = (
            db.query(Match)
            .filter(Match.id == first_match_id)
            .first()
        )

        from app.repositories.match_repository import MatchRepository

        repository = MatchRepository(db)
        analytics = TeamAnalytics(repository)

        generator = FeatureGenerator(analytics)

        features = generator.generate_match_features(first_match)

        print("\n========== MATCH FEATURES ==========\n")

        for key, value in features.items():
            print(f"{key:<30}: {value}")

    finally:
        builder.close()
        db.close()


if __name__ == "__main__":
    main()