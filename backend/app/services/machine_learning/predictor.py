import pandas as pd
from sklearn.base import ClassifierMixin

from app.services.machine_learning.model_manager import ModelManager


class Predictor:
    """
    Handles football match predictions using the best trained model.

    Responsibilities
    ----------------
    - Load the best trained model
    - Predict match outcomes
    - Predict outcome probabilities
    - Convert predictions into readable results
    """

    def __init__(self):
        """
        Initialize the prediction service.
        """

        # ==========================================================
        # Model Manager
        # ==========================================================

        self.model_manager = ModelManager()

        # ==========================================================
        # Trained Model
        # ==========================================================

        self.model: ClassifierMixin | None = None

        # ==========================================================
        # Prediction Labels
        # ==========================================================

        self.class_labels = {
            0: "Away Win",
            1: "Draw",
            2: "Home Win",
        }

        # ==========================================================
        # Prediction Results
        # ==========================================================

        self.predictions = None
        self.probabilities = None

    def load_model(self) -> ClassifierMixin:
        """
        Load the best trained machine learning model.

        Returns
        -------
        ClassifierMixin
            Loaded machine learning model.
        """

        print("=" * 70)
        print("Loading Best Model")
        print("=" * 70)

        self.model = self.model_manager.load_best_model()

        print(f"✓ Loaded {type(self.model).__name__}")

        return self.model

    def predict(
        self,
        features: pd.DataFrame,
    ):
        """
        Predict match outcomes.

        Parameters
        ----------
        features : pd.DataFrame
            Match features.

        Returns
        -------
        ndarray
            Predicted class labels.
        """

        if self.model is None:
            self.load_model()

        print()
        print("=" * 70)
        print("Predict Match Result")
        print("=" * 70)

        self.predictions = self.model.predict(features)

        print(f"✓ Generated {len(self.predictions)} prediction(s).")

        return self.predictions

    def predict_proba(
        self,
        features: pd.DataFrame,
    ):
        """
        Predict class probabilities.

        Parameters
        ----------
        features : pd.DataFrame
            Match features.

        Returns
        -------
        ndarray
            Prediction probabilities.
        """

        if self.model is None:
            self.load_model()

        print()
        print("=" * 70)
        print("Predict Match Probabilities")
        print("=" * 70)

        self.probabilities = self.model.predict_proba(features)

        print(
            f"✓ Generated probabilities for {len(self.probabilities)} prediction(s)."
        )

        return self.probabilities

    def predict_match(
        self,
        features: pd.DataFrame,
    ) -> dict:
        """
        Predict a football match result and return
        readable probabilities.

        Parameters
        ----------
        features : pd.DataFrame
            Match features.

        Returns
        -------
        dict
            Prediction summary.
        """

        predictions = self.predict(features)
        probabilities = self.predict_proba(features)

        # ---------------------------------------------------------
        # Handle CatBoost / XGBoost / LightGBM prediction formats
        # ---------------------------------------------------------

        prediction = predictions[0]

        if hasattr(prediction, "__len__"):
            prediction = prediction[0]

        prediction = int(prediction)

        probability = probabilities[0]

        # Classifier probability columns are ordered according to `classes_`.
        # Do not assume every estimator always exposes 0, 1, 2 in that order:
        # a training split can be missing a class, and different libraries can
        # expose classes differently.
        classes = getattr(self.model, "classes_", [0, 1, 2])
        probability_by_class = {
            int(class_id): float(value)
            for class_id, value in zip(classes, probability)
        }

        result = {
            "prediction": self.class_labels[prediction],
            "prediction_code": prediction,
            "probabilities": {
                "Away Win": round(probability_by_class.get(0, 0.0), 4),
                "Draw": round(probability_by_class.get(1, 0.0), 4),
                "Home Win": round(probability_by_class.get(2, 0.0), 4),
            },
        }

        return result

    def predict_batch(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Predict multiple football matches.

        Parameters
        ----------
        features : pd.DataFrame
            Match features.

        Returns
        -------
        pd.DataFrame
            Predictions with probabilities.
        """

        predictions = self.predict(features)
        probabilities = self.predict_proba(features)

        results = pd.DataFrame({
            "prediction_code": predictions,
            "prediction": [
                self.class_labels[prediction]
                for prediction in predictions
            ],
            "away_win_probability": probabilities[:, 0],
            "draw_probability": probabilities[:, 1],
            "home_win_probability": probabilities[:, 2],
        })

        return results

if __name__ == "__main__":

        predictor = Predictor()

        predictor.load_model()

        print()
        print("=" * 70)
        print("Predictor Ready")
        print("=" * 70)
