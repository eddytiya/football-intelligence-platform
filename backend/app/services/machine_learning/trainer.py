import pandas as pd

from sklearn.base import ClassifierMixin

from app.core.paths import PROCESSED_DATA_DIR
from app.services.machine_learning.model_factory import ModelFactory


# Identifiers are useful for linking a prediction to a fixture, but are not
# football signals. Including them teaches a model arbitrary database ordering.
NON_FEATURE_COLUMNS = {
    "match_result", "match_id", "home_team_id", "away_team_id",
    "match_date", "utc_date", "home_score", "away_score",
}


class Trainer:
    """
    Handles machine learning model training.

    Responsibilities
    ----------------
    - Load selected datasets
    - Prepare training data
    - Train machine learning models
    - Generate predictions
    - Later evaluate and save trained models
    """

    def __init__(self):
        """
        Initialize trainer configuration.
        """

        # ==========================================================
        # Dataset Directory
        # ==========================================================

        self.data_dir = PROCESSED_DATA_DIR

        # ==========================================================
        # Dataset Paths
        # ==========================================================

        self.train_path = self.data_dir / "train_processed.csv"
        self.validation_path = self.data_dir / "validation_processed.csv"
        self.test_path = self.data_dir / "test_processed.csv"

        # ==========================================================
        # Target Column
        # ==========================================================

        self.target_column = "match_result"

        # ==========================================================
        # DataFrames
        # ==========================================================

        self.train_df = None
        self.validation_df = None
        self.test_df = None

        # ==========================================================
        # Features
        # ==========================================================

        self.X_train = None
        self.X_validation = None
        self.X_test = None

        # ==========================================================
        # Targets
        # ==========================================================

        self.y_train = None
        self.y_validation = None
        self.y_test = None

        # ==========================================================
        # Model Information
        # ==========================================================

        self.model = None
        self.model_name = None

        # ==========================================================
        # Predictions
        # ==========================================================

        self.validation_predictions = None
        self.test_predictions = None

    def load_datasets(self):
        """
        Load selected datasets.
        """

        print("=" * 70)
        print("Loading Selected Datasets")
        print("=" * 70)

        self.train_df = pd.read_csv(self.train_path)
        self.validation_df = pd.read_csv(self.validation_path)
        self.test_df = pd.read_csv(self.test_path)

        print("✓ Training dataset loaded")
        print("✓ Validation dataset loaded")
        print("✓ Test dataset loaded")

        print()

        print("Dataset Shapes")
        print("-" * 70)
        print(f"Training   : {self.train_df.shape}")
        print(f"Validation : {self.validation_df.shape}")
        print(f"Test       : {self.test_df.shape}")

    def prepare_data(self):
        """
        Separate features and target column.
        """

        print()
        print("=" * 70)
        print("Preparing Features and Target")
        print("=" * 70)

        # Columns that should not be used as ML features
        columns_to_drop = list(NON_FEATURE_COLUMNS)

        # Drop only columns that exist
        self.X_train = self.train_df.drop(
            columns=columns_to_drop,
            errors="ignore",
        )
        self.y_train = self.train_df[self.target_column]

        self.X_validation = self.validation_df.drop(
            columns=columns_to_drop,
            errors="ignore",
        )
        self.y_validation = self.validation_df[self.target_column]

        self.X_test = self.test_df.drop(
            columns=columns_to_drop,
            errors="ignore",
        )
        self.y_test = self.test_df[self.target_column]

        print("✓ Training features prepared")
        print("✓ Validation features prepared")
        print("✓ Test features prepared")

        print()

        print(f"Training Features   : {self.X_train.shape}")
        print(f"Validation Features : {self.X_validation.shape}")
        print(f"Test Features       : {self.X_test.shape}")

        print()

        print(f"Training Target     : {self.y_train.shape}")
        print(f"Validation Target   : {self.y_validation.shape}")
        print(f"Test Target         : {self.y_test.shape}")

        from joblib import dump
        from app.core.paths import MODELS_DIR

        feature_columns_path = MODELS_DIR / "feature_columns.joblib"

        dump(
            list(self.X_train.columns),
            feature_columns_path,
        )

        print()
        print(f"✓ Saved feature columns -> {feature_columns_path}")
    def setup(self):
        """
        Load datasets and prepare them for training.
        """

        self.load_datasets()
        self.prepare_data()

    def train_model(
        self,
        model_name: str,
        **model_parameters,
    ) -> ClassifierMixin:
        """
        Train a single machine learning model.

        Parameters
        ----------
        model_name : str
            Name of the model to train.

        model_parameters : dict
            Optional model hyperparameters.

        Returns
        -------
        ClassifierMixin
            Trained machine learning model.
        """

        print()
        print("=" * 70)
        print(f"Training Model : {model_name}")
        print("=" * 70)

        # Store model name
        self.model_name = model_name

        # Create model
        self.model = ModelFactory.create(
            model_name,
            **model_parameters,
        )

        print(f"✓ Created {type(self.model).__name__}")

        print()
        print("Training model...")

        self.model.fit(
            self.X_train,
            self.y_train,
        )

        print("✓ Training completed")

        return self.model

    def predict_validation(self):
        """
        Predict the validation dataset.
        """

        print()
        print("=" * 70)
        print("Validation Prediction")
        print("=" * 70)

        self.validation_predictions = self.model.predict(
            self.X_validation
        )

        print(
            f"✓ Predicted {len(self.validation_predictions)} validation matches."
        )

        return self.validation_predictions

    def predict_test(self):
        """
        Predict the test dataset.
        """

        print()
        print("=" * 70)
        print("Test Prediction")
        print("=" * 70)

        self.test_predictions = self.model.predict(
            self.X_test
        )

        print(
            f"✓ Predicted {len(self.test_predictions)} test matches."
        )

        return self.test_predictions
