import pandas as pd

from app.services.machine_learning.trainer import Trainer
from app.services.machine_learning.evaluator import Evaluator
from app.services.machine_learning.model_manager import ModelManager


class ModelComparer:
    """
    Compare multiple machine learning models and rank them.

    Workflow
    --------
    Load datasets
        ↓
    Train each model
        ↓
    Predict validation set
        ↓
    Evaluate performance
        ↓
    Build leaderboard
        ↓
    Save best model
    """

    def __init__(self):
        self.trainer = Trainer()
        self.evaluator = Evaluator()
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

    def compare(self):
        """
        Compare all supported models.
        """

        print()
        print("=" * 70)
        print("MODEL COMPARISON")
        print("=" * 70)

        # Load dataset once
        self.trainer.setup()

        for model_name in self.models:

            print()
            print("=" * 70)
            print(f"Training {model_name}")
            print("=" * 70)

            self.trainer.train_model(model_name)

            predictions = self.trainer.predict_validation()

            metrics = self.evaluator.evaluate(
                self.trainer.y_validation,
                predictions,
            )

            self.results.append(
                {
                    "model": model_name,
                    "accuracy": metrics["accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"],
                    "model_object": self.trainer.model,
                }
            )

        self.print_leaderboard()

        self.save_best_model()

    def print_leaderboard(self):
        """
        Print comparison table.
        """

        leaderboard = pd.DataFrame(self.results)

        leaderboard = leaderboard.sort_values(
            by="accuracy",
            ascending=False,
        ).reset_index(drop=True)

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

        self.leaderboard = leaderboard

    def save_best_model(self):
        """
        Save the highest accuracy model.
        """

        best = self.leaderboard.iloc[0]

        self.model_manager.save_best_model(
            best["model_object"]
        )

        print()
        print("=" * 70)
        print(f"BEST MODEL : {best['model']}")
        print(f"Accuracy   : {best['accuracy']:.4f}")
        print("=" * 70)


if __name__ == "__main__":

    comparer = ModelComparer()

    comparer.compare()





    