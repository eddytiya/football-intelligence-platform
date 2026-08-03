from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.match import Match
from app.repositories.match_repository import MatchRepository
from app.services.feature_engineering.elo_rating import EloRatingService
from app.services.feature_engineering.feature_generator import FeatureGenerator
from app.services.feature_engineering.team_analytics import TeamAnalytics


class DatasetBuilder:
    """
    Builds the complete machine learning dataset.

    Responsibilities
    ----------------
    - Retrieve finished matches
    - Generate features for every match
    - Return a Pandas DataFrame

    This class DOES NOT:
    - Calculate football statistics
    - Execute SQL queries directly
    - Train ML models
    """

    def __init__(self):
        """
        Initialize all required services.
        """

        self.db: Session = SessionLocal()

        self.repository = MatchRepository(self.db)

        self.analytics = TeamAnalytics(self.repository)

        self.elo_service = EloRatingService()
        self.feature_generator = FeatureGenerator(self.analytics)

    def load_finished_matches(self) -> List[Match]:
        """
        Load all finished matches.
        """

        return self.repository.get_finished_matches()

    def build_dataset(self) -> pd.DataFrame:
        """
        Generate machine learning features for every finished match.
        """

        matches = self.load_finished_matches()

        dataset = []

        total_matches = len(matches)

        print(f"\nGenerating features for {total_matches} matches...\n")

        for index, match in enumerate(matches, start=1):

            print(f"Match {index}: Season {match.season_id}")

            # -----------------------------
            # Generate football features
            # -----------------------------
            features = self.feature_generator.generate_match_features(match)

            # -----------------------------
            # Elo BEFORE the match
            # -----------------------------
            elo_features = self.elo_service.get_match_features(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
            )

            features.update(elo_features)

            # -----------------------------
            # Target Variable
            # -----------------------------
            if match.home_score > match.away_score:
                features["match_result"] = 2      # Home Win

            elif match.home_score == match.away_score:
                features["match_result"] = 1      # Draw

            else:
                features["match_result"] = 0      # Away Win

            # Optional labels
            features["home_score"] = match.home_score
            features["away_score"] = match.away_score

            dataset.append(features)

            # -----------------------------
            # Update Elo AFTER the match
            # -----------------------------
            self.elo_service.update_elo(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                home_score=match.home_score,
                away_score=match.away_score,
                competition_code=(
                    match.competition.code
                    if match.competition
                    else None
                ),
            )

            if index % 100 == 0 or index == total_matches:
                print(f"Processed {index}/{total_matches} matches")

        print("\nFeature generation completed.\n")

        return pd.DataFrame(dataset)

    def save_dataset(
        self,
        file_path: str,
    ) -> None:
        """
        Generate and save the dataset.
        """

        dataset = self.build_dataset()

        dataset.to_csv(
            file_path,
            index=False,
        )

        print(f"\nDataset saved to:\n{file_path}")

    def close(self):
        """
        Close the database session.
        """

        self.db.close()


if __name__ == "__main__":

    builder = DatasetBuilder()

    try:

        dataset = builder.build_dataset()

        print("\n========== DATASET ==========\n")
        print(dataset.head())

        print("\n========== INFO ==========\n")
        dataset.info()

        print("\n========== SHAPE ==========\n")
        print(dataset.shape)

        print("\n========== COLUMNS ==========\n")
        print(dataset.columns.tolist())

        builder.save_dataset("football_dataset.csv")

    finally:

        builder.close()