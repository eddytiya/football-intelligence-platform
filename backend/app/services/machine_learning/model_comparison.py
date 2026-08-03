import pandas as pd

from app.services.machine_learning.model_manager import ModelManager
from app.services.machine_learning.training_pipeline import TrainingPipeline


class ModelComparison:
    """
    Train and compare multiple machine learning models.
    """

    def __init__(self):
        """
        Initialize model comparison.
        """

        self.pipeline = TrainingPipeline()
        self.model_manager = ModelManager()

        self.models = [
            "logistic_regression",
            "random_forest",
            "extra_trees",
            "gradient_boosting",
            "xgboost",
            "lightgbm",
            "catboost",
        ]

        self.results = []

    def train_all_models(self):
        """
        Train and evaluate every model.
        """

        self.results.clear()

        print()
        print("=" * 70)
        print("MODEL COMPARISON")
        print("=" * 70)

        for model_name in self.models:

            print()
            print("-" * 70)
            print(f"Running : {model_name}")
            print("-" * 70)

            result = self.pipeline.run(model_name)

            metrics = result["metrics"]
            metrics["model"] = model_name

            self.results.append(
                {
                    "model_name": model_name,
                    "model": result["model"],
                    "metadata": result["metadata"],
                    "metrics": metrics,
                }
            )

        return self.results

    def create_leaderboard(self):
        """
        Create a ranked leaderboard of all trained models.

        Returns
        -------
        pandas.DataFrame
            Leaderboard sorted by performance.
        """

        if not self.results:
            raise ValueError(
                "No model results found. Run train_all_models() first."
            )

        leaderboard = pd.DataFrame(
            [
                result["metrics"].copy()
                for result in self.results
            ]
        )

        leaderboard = leaderboard.sort_values(
            by=[
                "f1_score",
                "balanced_accuracy",
                "accuracy",
            ],
            ascending=False,
        ).reset_index(drop=True)

        leaderboard.index += 1

        return leaderboard

    def get_best_result(self):
        """
        Return the best trained model and its metadata.
        """

        leaderboard = self.create_leaderboard()

        best_model_name = leaderboard.iloc[0]["model"]

        for result in self.results:
            if result["model_name"] == best_model_name:
                return result

        raise ValueError("Best model not found.")

    def run(self):
        """
        Execute the complete model comparison workflow.

        Returns
        -------
        pandas.DataFrame
            Ranked model leaderboard.
        """

        self.train_all_models()

        leaderboard = self.create_leaderboard()

        self.model_manager.save_leaderboard(leaderboard)

        best_result = self.get_best_result()

        self.model_manager.save_best_model(
            best_result["model"]
        )

        self.model_manager.save_metadata(
            "best_model",
            best_result["metadata"],
        )

        print()
        print("=" * 90)
        print("MODEL LEADERBOARD")
        print("=" * 90)

        print(
            leaderboard[
                [
                    "model",
                    "accuracy",
                    "balanced_accuracy",
                    "precision",
                    "recall",
                    "f1_score",
                ]
            ]
        )

        print()
        print("=" * 90)
        print(f"BEST MODEL : {leaderboard.iloc[0]['model']}")
        print("=" * 90)

        return leaderboard