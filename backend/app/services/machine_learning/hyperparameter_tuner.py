import pandas as pd

from sklearn.model_selection import (
    StratifiedKFold,
    RandomizedSearchCV,
)
from app.services.machine_learning.model_manager import ModelManager
from app.core.paths import (
    PROCESSED_DATA_DIR,
    REPORTS_DIR,
)

from app.services.machine_learning.model_factory import (
    ModelFactory,
)
from pathlib import Path
import json


class HyperparameterTuner:
    """
    Performs hyperparameter tuning for the best
    machine learning models.

    Responsibilities
    ----------------
    - Load training dataset
    - Prepare features and target
    - Tune machine learning models
    - Compare tuned models
    - Save tuning results
    """

    def __init__(self):
        """
        Initialize tuner configuration.
        """

        # ==========================================================
        # Directories
        # ==========================================================

        self.data_dir = PROCESSED_DATA_DIR
        self.reports_dir = REPORTS_DIR

        # ==========================================================
        # Dataset
        # ==========================================================

        self.train_path = (
            self.data_dir /
            "train_processed.csv"
        )

        self.target_column = "match_result"

        self.train_df = None

        self.X = None
        self.y = None

        # ==========================================================
        # Cross Validation
        # ==========================================================

        self.cv = StratifiedKFold(
            n_splits=5,
            shuffle=True,
            random_state=42,
        )

        # ==========================================================
        # Models to Tune
        # ==========================================================

        self.models = [
            "catboost",
            "gradient_boosting",
            "xgboost",
        ]

        # ==========================================================
        # Results
        # ==========================================================

        self.results = []

        self.best_models = {}

    def load_dataset(self):
        """
        Load training dataset.
        """

        print("=" * 70)
        print("Loading Training Dataset")
        print("=" * 70)

        self.train_df = pd.read_csv(
            self.train_path
        )

        print("✓ Training dataset loaded")
        print(
            f"Shape : {self.train_df.shape}"
        )

    def prepare_data(self):
        """
        Prepare features and target.
        """

        print()
        print("=" * 70)
        print("Preparing Features and Target")
        print("=" * 70)

        # Columns that should not be used for training
        columns_to_drop = [
            "match_result",
            "match_id",
            "match_date",
        ]

        self.X = self.train_df.drop(
            columns=columns_to_drop,
            errors="ignore",
        )

        self.y = self.train_df[
            self.target_column
        ]

        print(
            f"Features : {self.X.shape}"
        )

        print(
            f"Target   : {self.y.shape}"
        )

        from joblib import dump
        from app.core.paths import MODELS_DIR

        feature_columns_path = (
            MODELS_DIR / "feature_columns.joblib"
        )

        dump(
            list(self.X.columns),
            feature_columns_path,
        )

        print()
        print(
            f"✓ Saved feature columns -> {feature_columns_path}"
        )

    def setup(self):
        """
        Prepare data for tuning.
        """

        self.load_dataset()
        self.prepare_data()

    def get_parameter_grid(
        self,
        model_name: str,
    ) -> dict:
        """
        Return the hyperparameter search space
        for a machine learning model.
        """

        parameter_grids = {

            "logistic_regression": {
                "C": [
                    0.01,
                    0.1,
                    1,
                    10,
                    100,
                ],
                "solver": [
                    "lbfgs",
                    "liblinear",
                ],
                "max_iter": [
                    500,
                    1000,
                    1500,
                ],
            },

            "lightgbm": {
                "n_estimators": [
                    200,
                    300,
                    500,
                    700,
                ],
                "learning_rate": [
                    0.01,
                    0.03,
                    0.05,
                    0.1,
                ],
                "max_depth": [
                    3,
                    5,
                    7,
                    10,
                ],
                "num_leaves": [
                    31,
                    50,
                    70,
                    100,
                ],
                "min_child_samples": [
                    10,
                    20,
                    30,
                    50,
                ],
                "subsample": [
                    0.8,
                    0.9,
                    1.0,
                ],
                "colsample_bytree": [
                    0.8,
                    0.9,
                    1.0,
                ],
            },

            "gradient_boosting": {
                "n_estimators": [
                    100,
                    200,
                    300,
                    500,
                ],
                "learning_rate": [
                    0.01,
                    0.03,
                    0.05,
                    0.1,
                ],
                "max_depth": [
                    3,
                    5,
                    7,
                ],
                "subsample": [
                    0.8,
                    0.9,
                    1.0,
                ],
            },

            "xgboost": {
                "n_estimators": [
                    200,
                    300,
                    500,
                    700,
                ],
                "learning_rate": [
                    0.01,
                    0.03,
                    0.05,
                    0.1,
                ],
                "max_depth": [
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                ],
                "subsample": [
                    0.8,
                    0.9,
                    1.0,
                ],
                "colsample_bytree": [
                    0.8,
                    0.9,
                    1.0,
                ],
                "min_child_weight": [
                    1,
                    3,
                    5,
                ],
            },

            "catboost": {
                "iterations": [
                    300,
                    500,
                    700,
                    1000,
                ],
                "learning_rate": [
                    0.01,
                    0.03,
                    0.05,
                    0.1,
                ],
                "depth": [
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                ],
                "l2_leaf_reg": [
                    1,
                    3,
                    5,
                    7,
                    9,
                ],
                "bagging_temperature": [
                    0,
                    0.5,
                    1,
                    2,
                    3,
                ],
                "random_strength": [
                    0,
                    1,
                    2,
                    5,
                ],
            },
        }

        return parameter_grids[model_name]

    def tune_model(
        self,
        model_name: str,
    ) -> dict:
        """
        Tune a machine learning model.
        """

        import time

        print()
        print("=" * 70)
        print(f"Tuning Model : {model_name}")
        print("=" * 70)

        start_time = time.time()

        model = ModelFactory.create(
            model_name
        )

        parameter_grid = self.get_parameter_grid(
            model_name
        )

        search = RandomizedSearchCV(
            estimator=model,
            param_distributions=parameter_grid,
            n_iter=50,
            scoring="f1_macro",
            cv=self.cv,
            random_state=42,
            n_jobs=-1,
            verbose=1,
            refit=True,
        )

        print("Searching best parameters...")

        search.fit(
            self.X,
            self.y,
        )

        elapsed_time = time.time() - start_time

        self.best_models[
            model_name
        ] = search.best_estimator_

        result = {
            "model": model_name,
            "best_score": search.best_score_,
            "best_parameters": search.best_params_,
            "training_time_seconds": round(elapsed_time, 2),
        }

        best_params_path = (
            self.reports_dir /
            f"{model_name}_best_parameters.json"
        )

        with open(best_params_path, "w") as file:
            json.dump(
                search.best_params_,
                file,
                indent=4,
            )

        print()
        print(f"✓ Best Score : {search.best_score_:.4f}")
        print(f"✓ Training Time : {elapsed_time:.2f} seconds")
        print(f"✓ Best parameters saved -> {best_params_path.name}")

        print()
        print("Best Parameters")
        print("-" * 70)

        for key, value in search.best_params_.items():
            print(f"{key}: {value}")

        return result

    def tune_all_models(self) -> pd.DataFrame:
        """
        Tune all configured machine learning models.

        Returns
        -------
        pd.DataFrame
            Hyperparameter tuning results.
        """

        print()
        print("=" * 70)
        print("Hyperparameter Tuning")
        print("=" * 70)

        self.results = []

        for model_name in self.models:

            result = self.tune_model(model_name)

            self.results.append(result)

        results_df = pd.DataFrame(self.results)

        results_df = results_df.sort_values(
            by="best_score",
            ascending=False,
        ).reset_index(drop=True)

        return results_df

    def save_results(
        self,
        results_df: pd.DataFrame,
    ):
        """
        Save hyperparameter tuning results.
        """

        file_path = (
            self.reports_dir /
            "hyperparameter_tuning_results.csv"
        )

        save_df = results_df.copy()

        save_df["best_parameters"] = (
            save_df["best_parameters"].astype(str)
        )

        save_df.to_csv(
            file_path,
            index=False,
        )

        print()
        print("=" * 70)
        print("Hyperparameter Tuning Complete")
        print("=" * 70)

        print(f"✓ Results saved : {file_path}")

        print()
        print("Leaderboard")
        print("-" * 70)

        print(
            save_df[
                [
                    "model",
                    "best_score",
                    "training_time_seconds",
                ]
            ]
        )

        best_result = save_df.iloc[0]

        print()
        print("=" * 70)
        print("BEST TUNED MODEL")
        print("=" * 70)
        print(f"Model         : {best_result['model']}")
        print(f"Best Score    : {best_result['best_score']:.4f}")
        print(
            f"Training Time : {best_result['training_time_seconds']} seconds"
        )

        return file_path

    def get_best_model(self):
        """
        Return the best tuned model.
        """

        if not self.results:
            raise ValueError(
                "No tuning results available."
            )

        best_model_name = max(
            self.results,
            key=lambda item: item["best_score"],
        )["model"]

        return (
            best_model_name,
            self.best_models[best_model_name],
        )

    def run(self):
        """
        Execute the complete hyperparameter tuning pipeline.
        """

        import time

        print()
        print("=" * 70)
        print("Starting Hyperparameter Tuning")
        print("=" * 70)

        start_time = time.time()

        # ---------------------------------------------------------
        # Prepare Dataset
        # ---------------------------------------------------------

        self.setup()

        # ---------------------------------------------------------
        # Tune Models
        # ---------------------------------------------------------

        results_df = self.tune_all_models()

        # ---------------------------------------------------------
        # Save Results
        # ---------------------------------------------------------

        self.save_results(results_df)

        # ---------------------------------------------------------
        # Best Model
        # ---------------------------------------------------------

        best_model_name, best_model = self.get_best_model()

        elapsed_time = time.time() - start_time

        print()
        print("=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"Best Model      : {best_model_name}")
        print(f"Best Score      : {results_df.iloc[0]['best_score']:.4f}")
        print(f"Models Tuned    : {len(self.models)}")
        print(f"Total Time      : {elapsed_time:.2f} seconds")
        print("=" * 70)

        return results_df