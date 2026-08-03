import json

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.core.paths import (
    MODELS_DIR,
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
)


class ModelEvaluator:
    """
    Evaluates the production machine learning model
    using the unseen test dataset.

    Responsibilities
    ----------------
    - Load trained model
    - Load test dataset
    - Prepare features
    - Generate predictions
    - Calculate evaluation metrics
    - Save evaluation reports
    """

    def __init__(self):
        """
        Initialize evaluator.
        """

        # ======================================================
        # Directories
        # ======================================================

        self.models_dir = MODELS_DIR
        self.processed_dir = PROCESSED_DATA_DIR
        self.reports_dir = REPORTS_DIR

        # ======================================================
        # Files
        # ======================================================

        self.model_path = (
            self.models_dir
            / "trained_models"
            / "best_model.joblib"
        )

        self.feature_columns_path = (
            self.models_dir /
            "feature_columns.joblib"
        )

        self.test_path = (
            self.processed_dir /
            "test_processed.csv"
        )

        self.target_column = "match_result"

        # ======================================================
        # Objects
        # ======================================================

        self.model = None

        self.feature_columns = None

        self.test_df = None

        self.X_test = None
        self.y_test = None

        self.predictions = None

        self.metrics = {}

    def load_model(self):
        """
        Load the production machine learning model.
        """

        print()
        print("=" * 70)
        print("Loading Production Model")
        print("=" * 70)

        self.model = joblib.load(
            self.model_path
        )

        print("✓ Model loaded successfully")

    def load_dataset(self):
        """
        Load the test dataset.
        """

        print()
        print("=" * 70)
        print("Loading Test Dataset")
        print("=" * 70)

        self.test_df = pd.read_csv(
            self.test_path
        )

        print("✓ Test dataset loaded")

        print(
            f"Dataset Shape : {self.test_df.shape}"
        )

    def prepare_data(self):
        """
        Prepare test features and target.
        """

        print()
        print("=" * 70)
        print("Preparing Test Data")
        print("=" * 70)

        # ---------------------------------------------------------
        # Load feature columns used during training
        # ---------------------------------------------------------

        self.feature_columns = joblib.load(
            self.feature_columns_path
        )

        print(
            f"Loaded {len(self.feature_columns)} feature columns"
        )

        # ---------------------------------------------------------
        # Prepare features
        # ---------------------------------------------------------

        self.X_test = self.test_df.reindex(
            columns=self.feature_columns,
            fill_value=0,
        )

        # ---------------------------------------------------------
        # Prepare target
        # ---------------------------------------------------------

        self.y_test = self.test_df[
            self.target_column
        ]

        print(
            f"Features Shape : {self.X_test.shape}"
        )

        print(
            f"Target Shape   : {self.y_test.shape}"
        )

    def setup(self):
        """
        Prepare everything required for evaluation.
        """

        self.load_model()

        self.load_dataset()

        self.prepare_data()

    def predict(self):
        """
        Generate predictions using the trained model.
        """

        print()
        print("=" * 70)
        print("Generating Predictions")
        print("=" * 70)

        self.predictions = self.model.predict(
            self.X_test
        )

        print(
            f"✓ Generated {len(self.predictions)} predictions"
        )

    def evaluate(self):
        """
        Evaluate model performance.
        """

        print()
        print("=" * 70)
        print("Evaluating Model")
        print("=" * 70)

        self.metrics = {
            "accuracy": accuracy_score(
                self.y_test,
                self.predictions,
            ),
            "balanced_accuracy": balanced_accuracy_score(
                self.y_test,
                self.predictions,
            ),
            "precision": precision_score(
                self.y_test,
                self.predictions,
                average="macro",
                zero_division=0,
            ),
            "recall": recall_score(
                self.y_test,
                self.predictions,
                average="macro",
                zero_division=0,
            ),
            "f1_score": f1_score(
                self.y_test,
                self.predictions,
                average="macro",
                zero_division=0,
            ),
        }

        print()
        print("Evaluation Metrics")
        print("-" * 70)

        for metric, value in self.metrics.items():
            print(
                f"{metric:<20}: {value:.4f}"
            )

    def save_reports(self):
        """
        Save evaluation reports.
        """

        print()
        print("=" * 70)
        print("Saving Reports")
        print("=" * 70)

        # ======================================================
        # Metrics JSON
        # ======================================================

        metrics_path = (
            self.reports_dir /
            "test_metrics.json"
        )

        with open(metrics_path, "w") as file:
            json.dump(
                self.metrics,
                file,
                indent=4,
            )

        print(
            f"✓ Saved {metrics_path.name}"
        )

        # ======================================================
        # Classification Report
        # ======================================================

        report = classification_report(
            self.y_test,
            self.predictions,
            zero_division=0,
        )

        report_path = (
            self.reports_dir /
            "classification_report.txt"
        )

        with open(report_path, "w") as file:
            file.write(report)

        print(
            f"✓ Saved {report_path.name}"
        )

        # ======================================================
        # Confusion Matrix
        # ======================================================

        matrix = confusion_matrix(
            self.y_test,
            self.predictions,
        )

        matrix_df = pd.DataFrame(matrix)

        matrix_path = (
            self.reports_dir /
            "confusion_matrix.csv"
        )

        matrix_df.to_csv(
            matrix_path,
            index=False,
        )

        print(
            f"✓ Saved {matrix_path.name}"
        )

        # ======================================================
        # Feature Importance
        # ======================================================

        if hasattr(
            self.model,
            "feature_importances_",
        ):

            importance_df = pd.DataFrame(
                {
                    "feature": self.feature_columns,
                    "importance": self.model.feature_importances_,
                }
            )

            importance_df = (
                importance_df.sort_values(
                    by="importance",
                    ascending=False,
                )
            )

            importance_path = (
                self.reports_dir /
                "feature_importance.csv"
            )

            importance_df.to_csv(
                importance_path,
                index=False,
            )

            print(
                f"✓ Saved {importance_path.name}"
            )

    def run(self):
        """
        Execute the complete evaluation pipeline.
        """

        print()
        print("=" * 70)
        print("MODEL EVALUATION PIPELINE")
        print("=" * 70)

        self.setup()

        self.predict()

        self.evaluate()

        self.save_reports()

        print()
        print("=" * 70)
        print("MODEL EVALUATION COMPLETE")
        print("=" * 70)

        return self.metrics


if __name__ == "__main__":

    evaluator = ModelEvaluator()

    metrics = evaluator.run()

    print()
    print("=" * 70)
    print("FINAL TEST METRICS")
    print("=" * 70)

    for metric, value in metrics.items():
        print(f"{metric:<20}: {value:.4f}")