import joblib
import pandas as pd

from app.core.paths import MODELS_DIR
from app.models.match import Match
from app.repositories.match_repository import MatchRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.feature_engineering.feature_generator import FeatureGenerator
from app.services.feature_engineering.team_analytics import TeamAnalytics


class PredictionService:
    """
    Service responsible for generating machine
    learning predictions for football matches.

    Responsibilities
    ----------------
    - Load production model
    - Generate ML features
    - Predict outcomes
    - Save predictions
    - Retrieve predictions

    This service DOES NOT:
    - Train models
    - Perform ETL
    - Access database directly
    """

    def __init__(
        self,
        prediction_repository: PredictionRepository,
        match_repository: MatchRepository,
        team_analytics: TeamAnalytics,
    ):
        """
        Initialize prediction service.
        """

        self.prediction_repository = (
            prediction_repository
        )

        self.match_repository = (
            match_repository
        )

        self.team_analytics = (
            team_analytics
        )

        # =====================================================
        # Load production model
        # =====================================================

        self.model = joblib.load(
            MODELS_DIR
            / "trained_models"
            / "best_model.joblib"
        )

        self.feature_columns = joblib.load(
            MODELS_DIR / "feature_columns.joblib"
        )

        self.model_name = (
            self.model.__class__.__name__
        )

        # =====================================================
        # Feature Generator
        # =====================================================

        self.feature_generator = FeatureGenerator(
            analytics=self.team_analytics
        )

    def prepare_features(
        self,
        match: Match,
    ) -> pd.DataFrame:
        """
        Generate ML features for a future match.
        """

        print()
        print("=" * 70)
        print("Preparing Match Features")
        print("=" * 70)

        features = (
            self.feature_generator.generate_prediction_features(
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                match_date=match.utc_date,
            )
        )

        # ---------------------------------------------
        # Convert dictionary to DataFrame
        # ---------------------------------------------

        features_df = pd.DataFrame(
            [features]
        )

        # ---------------------------------------------
        # Keep the same feature order used
        # during model training
        # ---------------------------------------------

        features_df = features_df.reindex(
            columns=self.feature_columns,
            fill_value=0,
        )

        print(
            f"Prepared {features_df.shape[1]} features"
        )

        return features_df

    def predict_match(
        self,
        match_id: int,
        save_prediction: bool = True,
    ) -> dict:
        """
        Predict a single football match.

        Returns
        -------
        dict
            Prediction result.
        """

        print()
        print("=" * 70)
        print(f"Predicting Match {match_id}")
        print("=" * 70)

        match = self.match_repository.get_match_by_id(
            match_id
        )

        if match is None:

            raise ValueError(
                f"Match {match_id} not found."
            )

        features = self.prepare_features(
            match
        )

        prediction = self.model.predict(
            features
        )

        # Convert NumPy output to a Python integer
        prediction = int(prediction.ravel()[0])

        probabilities = self.model.predict_proba(
            features
        )[0]

        labels = {
            2: "HOME_WIN",
            1: "DRAW",
            0: "AWAY_WIN",
        }

        result = {
            "match_id": match.id,
            "model": self.model_name,
            "prediction": labels[prediction],
            "home_probability": float(
                probabilities[2]
            ),
            "draw_probability": float(
                probabilities[1]
            ),
            "away_probability": float(
                probabilities[0]
            ),
        }

        if save_prediction:

            self.prediction_repository.save_prediction(
                match_id=match.id,
                model_name=self.model_name,
                prediction=result["prediction"],
                home_probability=result[
                    "home_probability"
                ],
                draw_probability=result[
                    "draw_probability"
                ],
                away_probability=result[
                    "away_probability"
                ],
            )

        print("Prediction completed.")

        return result

    def predict_matches(
        self,
        match_ids: list[int],
        save_predictions: bool = True,
    ) -> list[dict]:
        """
        Predict multiple matches.
        """

        print()
        print("=" * 70)
        print("Predicting Multiple Matches")
        print("=" * 70)

        predictions = []

        for match_id in match_ids:

            try:

                prediction = self.predict_match(
                    match_id=match_id,
                    save_prediction=save_predictions,
                )

                predictions.append(
                    prediction
                )

            except Exception as error:

                print(
                    f"Failed to predict match {match_id}: {error}"
                )

        print()

        print(
            f"Generated {len(predictions)} predictions."
        )

        return predictions

    def predict_upcoming_matches(
        self,
        days: int = 7,
        save_predictions: bool = True,
    ) -> list[dict]:
        """
        Predict all upcoming matches.
        """

        print()
        print("=" * 70)
        print("Predict Upcoming Matches")
        print("=" * 70)

        matches = (
            self.match_repository.get_upcoming_matches()
        )

        print("=" * 70)
        print(f"Upcoming Matches Returned : {len(matches)}")
        print("=" * 70)

        predictions = []

        for match in matches:

            prediction = self.predict_match(
                match_id=match.id,
                save_prediction=save_predictions,
            )

            predictions.append(
                prediction
            )

        return predictions

    def get_prediction(
        self,
        match_id: int,
    ):
        """
        Return prediction for a match.
        """

        return (
            self.prediction_repository
            .get_prediction_by_match_id(
                match_id
            )
        )

    def get_today_predictions(
        self,
    ):
        """
        Return today's predictions.
        """

        return (
            self.prediction_repository
            .get_todays_predictions()
        )

    

    def delete_old_predictions(
        self,
        days: int = 30,
    ) -> int:
        """
        Delete old predictions.
        """

        from datetime import datetime, timedelta

        cutoff = (
            datetime.utcnow() -
            timedelta(days=days)
        )

        return (
            self.prediction_repository
            .delete_old_predictions(
                before_date=cutoff,
            )
        )

    def run_prediction_pipeline(
        self,
        days: int = 7,
    ):
        """
        Execute the complete prediction pipeline.
        """

        print()
        print("=" * 70)
        print("Prediction Pipeline")
        print("=" * 70)

        predictions = (
            self.predict_upcoming_matches(
                days=days,
            )
        )

        print()

        print("=" * 70)
        print("Prediction Pipeline Complete")
        print("=" * 70)

        print(
            f"Generated {len(predictions)} predictions."
        )

        return predictions