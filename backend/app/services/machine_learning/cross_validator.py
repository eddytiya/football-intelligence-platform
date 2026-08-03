import pandas as pd

from sklearn.model_selection import TimeSeriesSplit, cross_validate

from app.core.paths import PROCESSED_DATA_DIR, REPORTS_DIR
from app.services.machine_learning.model_factory import ModelFactory
from app.services.machine_learning.trainer import NON_FEATURE_COLUMNS


class CrossValidator:
    """
    Performs cross-validation for all supported machine learning models.

    Responsibilities
    ----------------
    - Load training dataset
    - Prepare features and target
    - Perform chronological walk-forward validation
    - Evaluate multiple models
    - Save comparison results
    """

    def __init__(self):
        """
        Initialize cross validation configuration.
        """

        # ==========================================================
        # Directories
        # ==========================================================

        self.data_dir = PROCESSED_DATA_DIR
        self.reports_dir = REPORTS_DIR

        # ==========================================================
        # Dataset
        # ==========================================================

        self.train_path = self.data_dir / "train_selected.csv"

        self.target_column = "match_result"

        self.train_df = None

        self.X = None
        self.y = None

        # ==========================================================
        # Cross Validation
        # ==========================================================

        self.cv = TimeSeriesSplit(n_splits=5)

        # ==========================================================
        # Models
        # ==========================================================

        self.models = [
            "logistic_regression",
            "random_forest",
            "extra_trees",
            "gradient_boosting",
            "xgboost",
            "lightgbm",
            "catboost",
        ]

        # ==========================================================
        # Results
        # ==========================================================

        self.results = []

    def load_dataset(self):
        """
        Load training dataset.
        """

        print("=" * 70)
        print("Loading Training Dataset")
        print("=" * 70)

        self.train_df = pd.read_csv(self.train_path)

        print("✓ Training dataset loaded")
        print(f"Shape : {self.train_df.shape}")

    def prepare_data(self):
        """
        Prepare features and target.
        """

        print()
        print("=" * 70)
        print("Preparing Features and Target")
        print("=" * 70)

        self.X = self.train_df.drop(columns=list(NON_FEATURE_COLUMNS), errors="ignore")

        self.y = self.train_df[self.target_column]

        print(f"Features : {self.X.shape}")
        print(f"Target   : {self.y.shape}")

    def setup(self):
        """
        Prepare dataset for cross validation.
        """

        self.load_dataset()
        self.prepare_data()

    def evaluate_model(
        self,
        model_name: str,
    ) -> dict:
        """
        Perform Stratified K-Fold Cross Validation for one model.

        Parameters
        ----------
        model_name : str
            Name of the machine learning model.

        Returns
        -------
        dict
            Cross-validation metrics.
        """

        print()
        print("=" * 70)
        print(f"Cross Validating : {model_name}")
        print("=" * 70)

        model = ModelFactory.create(model_name)

        scoring = {
            "accuracy": "accuracy",
            "balanced_accuracy": "balanced_accuracy",
            "precision": "precision_macro",
            "recall": "recall_macro",
            "f1": "f1_macro",
            "neg_log_loss": "neg_log_loss",
        }

        scores = cross_validate(
            estimator=model,
            X=self.X,
            y=self.y,
            cv=self.cv,
            scoring=scoring,
            n_jobs=-1,
            return_train_score=False,
        )

        result = {
            "model": model_name,
            "accuracy_mean": scores["test_accuracy"].mean(),
            "accuracy_std": scores["test_accuracy"].std(),
            "balanced_accuracy_mean": scores["test_balanced_accuracy"].mean(),
            "balanced_accuracy_std": scores["test_balanced_accuracy"].std(),
            "precision_mean": scores["test_precision"].mean(),
            "precision_std": scores["test_precision"].std(),
            "recall_mean": scores["test_recall"].mean(),
            "recall_std": scores["test_recall"].std(),
            "f1_mean": scores["test_f1"].mean(),
            "f1_std": scores["test_f1"].std(),
            "log_loss_mean": -scores["test_neg_log_loss"].mean(),
            "log_loss_std": scores["test_neg_log_loss"].std(),
        }

        print(
            f"Accuracy : {result['accuracy_mean']:.4f} ± {result['accuracy_std']:.4f}"
        )

        print(
            f"Precision: {result['precision_mean']:.4f} ± {result['precision_std']:.4f}"
        )

        print(
            f"Recall   : {result['recall_mean']:.4f} ± {result['recall_std']:.4f}"
        )

        print(
            f"F1 Score : {result['f1_mean']:.4f} ± {result['f1_std']:.4f}"
        )

        return result

    def evaluate_all_models(self) -> pd.DataFrame:
        """
        Evaluate every supported machine learning model.

        Returns
        -------
        pd.DataFrame
            Cross-validation comparison table.
        """

        print()
        print("=" * 70)
        print("Cross Validating All Models")
        print("=" * 70)

        self.results = []

        for model_name in self.models:

            result = self.evaluate_model(model_name)

            self.results.append(result)

        results_df = pd.DataFrame(self.results)

        results_df = results_df.sort_values(
            by="f1_mean",
            ascending=False,
        ).reset_index(drop=True)

        return results_df

    def save_results(
        self,
        results_df: pd.DataFrame,
    ):
        """
        Save cross-validation results.
        """

        file_path = (
            self.reports_dir /
            "cross_validation_results.csv"
        )

        results_df.to_csv(
            file_path,
            index=False,
        )

        print()
        print("=" * 70)
        print("Cross Validation Complete")
        print("=" * 70)

        print(f"✓ Results saved : {file_path.name}")

        print()
        print("Leaderboard")
        print("-" * 70)

        print(
            results_df[
                [
                    "model",
                    "accuracy_mean",
                    "precision_mean",
                    "recall_mean",
                    "f1_mean",
                ]
            ]
        )

        return file_path

    def run(self):
        """
        Execute the complete cross-validation pipeline.
        """

        self.setup()

        results_df = self.evaluate_all_models()

        self.save_results(results_df)

        return results_df

if __name__ == "__main__":

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Machine Learning - Cross Validation")
    print("=" * 70)

    validator = CrossValidator()

    leaderboard = validator.run()

    print()
    print("=" * 70)
    print("Final Cross Validation Leaderboard")
    print("=" * 70)

    print(leaderboard)

    print()
    print("✓ Cross validation completed successfully.")
