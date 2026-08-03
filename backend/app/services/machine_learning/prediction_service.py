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


class PredictionService:
    """
    Builds machine learning features and generates
    predictions for football matches.
    """

    def __init__(self, db: Session):
        """
        Initialize the prediction service.
        """

        # ==========================================================
        # Database
        # ==========================================================

        self.db = db

        # ==========================================================
        # Repositories
        # ==========================================================

        self.repository = MatchRepository(db)

        self.prediction_repository = PredictionRepository(db)

        # ==========================================================
        # Analytics
        # ==========================================================

        self.analytics = TeamAnalytics(
            self.repository
        )

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

    # ==========================================================
    # Feature Builder
    # ==========================================================

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
    ) -> dict:
        """
        Predict a football match and save the prediction.

        Parameters
        ----------
        match_id : int
            Match database ID.

        Returns
        -------
        dict
            Prediction result.
        """

        # ==========================================================
        # Retrieve Match
        # ==========================================================

        match = self.repository.get_match_by_id(
            match_id
        )

        if match is None:
            raise ValueError(
                f"Match with ID {match_id} not found."
            )

        # ==========================================================
        # Build Features
        # ==========================================================

        features = self.build_features(
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
        )

        # ==========================================================
        # Predict Match
        # ==========================================================

        result = self.predictor.predict_match(
            features
        )

        # ==========================================================
        # Save Prediction
        # ==========================================================

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

        # ==========================================================
        # Return Prediction
        # ==========================================================

        return result

        # ==========================================================
    # Prediction Retrieval
    # ==========================================================

    def get_prediction(
        self,
        prediction_id: int,
    ):
        """
        Return a prediction by its ID.
        """

        return self.prediction_repository.get_prediction_by_id(
            prediction_id
        )

    def get_match_prediction(
        self,
        match_id: int,
    ):
        """
        Return prediction for a match.
        """

        return self.prediction_repository.get_prediction_by_match_id(
            match_id
        )

    def get_competition_predictions(
        self,
        competition_id: int,
    ):
        """
        Return predictions for a competition.
        """

        return self.prediction_repository.get_predictions_by_competition(
            competition_id
        )

    def get_todays_predictions(
        self,
    ):
        """
        Return today's predictions.
        """

        return self.prediction_repository.get_todays_predictions()

    def delete_prediction(
        self,
        prediction_id: int,
    ) -> bool:
        """
        Delete a prediction by its ID.
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