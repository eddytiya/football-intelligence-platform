from datetime import datetime

import pandas as pd
from joblib import load
from sqlalchemy.orm import Session

from app.core.paths import MODELS_DIR
from app.repositories.match_repository import MatchRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.feature_engineering.feature_generator import FeatureGenerator
from app.services.feature_engineering.team_analytics import TeamAnalytics
from app.services.machine_learning.predictor import Predictor
from app.schemas.prediction import PredictionDetail


class PredictionService:
    """
    Builds machine learning features and manages
    football match predictions.
    """

    def __init__(self, db: Session):
        """
        Initialize the prediction service.
        """

        # ==========================================================
        # Repositories
        # ==========================================================

        self.repository = MatchRepository(db)
        self.prediction_repository = PredictionRepository(db)

        # ==========================================================
        # Analytics
        # ==========================================================

        self.analytics = TeamAnalytics(self.repository)

        # ==========================================================
        # Feature Generator
        # ==========================================================

        self.feature_generator = FeatureGenerator(
            self.analytics
        )

        # ==========================================================
        # Predictor
        # ==========================================================

        self.predictor = Predictor()

        # ==========================================================
        # Feature Columns
        # ==========================================================

        self.feature_columns = load(
            MODELS_DIR / "feature_columns.joblib"
        )

    def build_features(
        self,
        home_team_id: int,
        away_team_id: int,
    ) -> pd.DataFrame:
        """
        Generate prediction features for a match.
        """

        features = self.feature_generator.generate_prediction_features(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_date=datetime.utcnow(),
        )

        dataframe = pd.DataFrame([features])

        dataframe = dataframe.reindex(
            columns=self.feature_columns,
            fill_value=0,
        )

        print("\n" + "=" * 70)
        print("Prediction Features")
        print("=" * 70)

        print(dataframe.dtypes)

        print("\nObject Columns:")
        print(
            dataframe.select_dtypes(
                include=["object"]
            ).columns.tolist()
        )

        print("\nFeature Values:")
        print(dataframe.head())

        return dataframe

    # ==========================================================
    # Prediction
    # ==========================================================

    def predict_match(
        self,
        match_id: int,
    ):
        """
        Generate and save a prediction for a match.
        """

        match = self.repository.get_match_by_id(match_id)

        if match is None:
            raise ValueError(
                f"Match {match_id} not found."
            )

        features = self.build_features(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
        )

        result = self.predictor.predict_match(
            features
        )

        self.prediction_repository.save_prediction(
            match_id=match.id,
            model_name=type(
                self.predictor.model
            ).__name__,
            prediction=result["prediction"],
            home_probability=result["probabilities"]["Home Win"],
            draw_probability=result["probabilities"]["Draw"],
            away_probability=result["probabilities"]["Away Win"],
        )

        return result
    
        # ==========================================================
    # Batch Prediction
    # ==========================================================

    def predict_matches(
        self,
        match_ids: list[int],
    ):
        """
        Generate predictions for multiple matches.

        Parameters
        ----------
        match_ids : list[int]
            List of match IDs.

        Returns
        -------
        list
            Prediction results.
        """

        predictions = []

        for match_id in match_ids:

            match = self.repository.get_match_by_id(
                match_id
            )

            if match is None:
                continue

            result = self.predict_match(
                match_id
            )

            predictions.append(
                {
                    "match_id": match.id,
                    "prediction": result["prediction"],
                    "prediction_code": result["prediction_code"],
                    "home_probability": result["probabilities"]["Home Win"],
                    "draw_probability": result["probabilities"]["Draw"],
                    "away_probability": result["probabilities"]["Away Win"],
                }
            )

        return predictions

    def predict_upcoming_matches(
        self,
        days: int = 7,
    ):
        """
        Generate predictions for all upcoming matches.
        """

        print()
        print("=" * 70)
        print("Predict Upcoming Matches")
        print("=" * 70)

        matches = self.repository.get_upcoming_matches(
            days=days,
            limit=10,
        )

        print(
            f"Upcoming Matches : {len(matches)}"
        )

        predictions = []

        for match in matches:

            result = self.predict_match(
                match.id
            )

            predictions.append(
                {
                    "match_id": match.id,
                    "prediction": result["prediction"],
                    "prediction_code": result["prediction_code"],
                    "home_probability": result["probabilities"]["Home Win"],
                    "draw_probability": result["probabilities"]["Draw"],
                    "away_probability": result["probabilities"]["Away Win"],
                }
            )

        return predictions
    # ==========================================================
    # Helper Methods
    # ==========================================================

    def _build_prediction_detail(
        self,
        prediction,
    ) -> PredictionDetail:
        """
        Convert a Prediction ORM object into a PredictionDetail.
        """

        match = prediction.match

        return PredictionDetail(
            # ==========================================================
            # Prediction Information
            # ==========================================================

            id=prediction.id,
            match_id=prediction.match_id,

            model_name=prediction.model_name,
            prediction=prediction.prediction,

            home_probability=prediction.home_probability,
            draw_probability=prediction.draw_probability,
            away_probability=prediction.away_probability,

            predicted_at=prediction.predicted_at,

            # ==========================================================
            # Competition Information
            # ==========================================================

            competition_name=match.competition.name,
            competition_code=match.competition.code,
            competition_emblem=match.competition.emblem,

            # ==========================================================
            # Home Team Information
            # ==========================================================

            home_team_name=match.home_team.name,
            home_team_crest=match.home_team.crest,

            # ==========================================================
            # Away Team Information
            # ==========================================================

            away_team_name=match.away_team.name,
            away_team_crest=match.away_team.crest,

            # ==========================================================
            # Match Information
            # ==========================================================

            utc_date=match.utc_date,
        )

    # ==========================================================
    # Prediction Retrieval
    # ==========================================================

    def get_prediction(
        self,
        prediction_id: int,
    ):
        """
        Return a prediction by ID.
        """

        prediction = (
            self.prediction_repository.get_prediction_by_id(
                prediction_id
            )
        )

        if prediction is None:
            return None

        return self._build_prediction_detail(
            prediction
        )

    def get_match_prediction(
        self,
        match_id: int,
    ):
        """
        Return prediction for a match.
        """

        prediction = (
            self.prediction_repository.get_prediction_by_match_id(
                match_id
            )
        )

        if prediction is None:
            return None

        return self._build_prediction_detail(
            prediction
        )

    def get_competition_predictions(
        self,
        competition_id: int,
    ):
        """
        Return predictions for a competition.
        """

        predictions = (
            self.prediction_repository.get_predictions_by_competition(
                competition_id
            )
        )

        return [
            self._build_prediction_detail(
                prediction
            )
            for prediction in predictions
        ]

    def get_todays_predictions(
        self,
    ):
        """
        Return today's predictions.
        """

        predictions = (
            self.prediction_repository.get_todays_predictions()
        )

        return [
            self._build_prediction_detail(
                prediction
            )
            for prediction in predictions
        ]

    # ==========================================================
    # Delete
    # ==========================================================

    def delete_prediction(
        self,
        prediction_id: int,
    ) -> bool:
        """
        Delete a prediction.
        """

        prediction = (
            self.prediction_repository.get_prediction_by_id(
                prediction_id
            )
        )

        if prediction is None:
            return False

        self.prediction_repository.delete_prediction(
            prediction
        )

        return True