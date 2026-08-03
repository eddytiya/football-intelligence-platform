from pathlib import Path

import pandas as pd


class Preprocessing:
   

    def __init__(self):

        # ======================================================
        # Project Paths
        # ======================================================

        self.base_path = Path(__file__).resolve().parents[3]

        self.splits_path = self.base_path / "data" / "splits"

        self.processed_path = self.base_path / "data" / "processed"

        self.processed_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ======================================================
        # Dataset Paths
        # ======================================================

        self.train_path = self.splits_path / "train.csv"

        self.validation_path = self.splits_path / "validation.csv"

        self.test_path = self.splits_path / "test.csv"

        # ======================================================
        # Raw Split Datasets
        # ======================================================

        self.train_dataset = pd.DataFrame()

        self.validation_dataset = pd.DataFrame()

        self.test_dataset = pd.DataFrame()

        # ======================================================
        # Feature / Target
        # ======================================================

        self.target_column = "match_result"

        self.date_column = "match_date"

        # ======================================================
        # Feature Matrices
        # ======================================================

        self.X_train = pd.DataFrame()
        self.X_validation = pd.DataFrame()
        self.X_test = pd.DataFrame()

        # ======================================================
        # Target Vectors
        # ======================================================

        self.y_train = pd.Series(dtype="int64")
        self.y_validation = pd.Series(dtype="int64")
        self.y_test = pd.Series(dtype="int64")

        # ======================================================
        # Processed Dataset Paths
        # ======================================================

        self.processed_train_path = (
            self.processed_path / "train_processed.csv"
        )

        self.processed_validation_path = (
            self.processed_path / "validation_processed.csv"
        )

        self.processed_test_path = (
            self.processed_path / "test_processed.csv"
        )



    # ==========================================================
    # STEP 1: Load Dataset Splits
    # ==========================================================

    def load_datasets(self) -> None:
        """
        Load the train, validation, and test datasets.
        """

        print("=" * 70)
        print("Football Intelligence Platform")
        print("Machine Learning - Preprocessing")
        print("=" * 70)

        print(f"Project Path : {self.base_path}")
        print(f"Splits Path  : {self.splits_path}")

        print("\n[STEP 1] Loading dataset splits...")

        # ------------------------------------------------------
        # Load datasets
        # ------------------------------------------------------

        self.train_dataset = pd.read_csv(
            self.train_path,
            parse_dates=[self.date_column],
        )
        print(self.train_dataset.columns.tolist())

        self.validation_dataset = pd.read_csv(
            self.validation_path,
            parse_dates=[self.date_column],
        )

        self.test_dataset = pd.read_csv(
            self.test_path,
            parse_dates=[self.date_column],
        )

        print("✓ Dataset splits loaded successfully.\n")

        print("Dataset Shapes")
        print("-" * 70)

        print(
            f"Training   : {self.train_dataset.shape}"
        )

        print(
            f"Validation : {self.validation_dataset.shape}"
        )

        print(
            f"Test       : {self.test_dataset.shape}"
        )

    # ==========================================================
    # STEP 2: Separate Features and Target
    # ==========================================================

    def separate_features_and_target(self) -> None:
        """
        Separate the feature matrices (X) and target vectors (y).
        """

        print("\n" + "=" * 70)
        print("SEPARATE FEATURES AND TARGET")
        print("=" * 70)

        # ------------------------------------------------------
        # Columns to Drop
        # ------------------------------------------------------

        drop_columns = [
            self.target_column,
            self.date_column,
            "match_id",
            "home_team_id",
            "away_team_id",
        ]

        # Only drop columns that actually exist
        drop_columns = [
            column
            for column in drop_columns
            if column in self.train_dataset.columns
        ]

        # ------------------------------------------------------
        # Training Dataset
        # ------------------------------------------------------

        self.X_train = self.train_dataset.drop(
            columns=drop_columns,
            errors="ignore",
        )

        self.y_train = self.train_dataset[
            self.target_column
        ]

        # ------------------------------------------------------
        # Validation Dataset
        # ------------------------------------------------------

        self.X_validation = self.validation_dataset.drop(
            columns=drop_columns,
            errors="ignore",
        )

        self.y_validation = self.validation_dataset[
            self.target_column
        ]

        # ------------------------------------------------------
        # Test Dataset
        # ------------------------------------------------------

        self.X_test = self.test_dataset.drop(
            columns=drop_columns,
            errors="ignore",
        )

        self.y_test = self.test_dataset[
            self.target_column
        ]

        print("✓ Features and target separated successfully.\n")

        print("Feature Matrix Shapes")
        print("-" * 70)
        print(f"X_train      : {self.X_train.shape}")
        print(f"X_validation : {self.X_validation.shape}")
        print(f"X_test       : {self.X_test.shape}")

        print("\nTarget Shapes")
        print("-" * 70)
        print(f"y_train      : {self.y_train.shape}")
        print(f"y_validation : {self.y_validation.shape}")
        print(f"y_test       : {self.y_test.shape}")

    def handle_missing_values(self) -> None:
        """
        Fill missing values in numerical columns.
        """

        print("\n" + "=" * 70)
        print("HANDLE MISSING VALUES")
        print("=" * 70)

        self.X_train = self.X_train.fillna(0)
        self.X_validation = self.X_validation.fillna(0)
        self.X_test = self.X_test.fillna(0)

        print("✓ Missing values filled with 0.")

        # ==========================================================
    # STEP 3: Inspect Features
    # ==========================================================

    def inspect_features(self) -> None:
        """
        Inspect the feature matrices before preprocessing.
        """

        print("\n" + "=" * 70)
        print("FEATURE INSPECTION")
        print("=" * 70)

        print(f"Number of Features : {len(self.X_train.columns)}")

        print("\nFirst 10 Features")
        print("-" * 70)

        for index, column in enumerate(self.X_train.columns[:10], start=1):
            print(f"{index:2}. {column}")

        print("\nLast 10 Features")
        print("-" * 70)

        total_features = len(self.X_train.columns)

        for index, column in enumerate(
            self.X_train.columns[-10:],
            start=total_features - 9,
        ):
            print(f"{index:3}. {column}")

        # ==========================================================
    # STEP 4: Identify Feature Types
    # ==========================================================

    def identify_feature_types(self) -> None:
        """
        Identify numerical and categorical feature columns.
        """

        print("\n" + "=" * 70)
        print("FEATURE TYPE SUMMARY")
        print("=" * 70)

        numerical_columns = self.X_train.select_dtypes(
            include=["number"]
        ).columns.tolist()

        categorical_columns = self.X_train.select_dtypes(
            include=["object", "string", "category"]
        ).columns.tolist()

        print(f"Numerical Features  : {len(numerical_columns)}")
        print(f"Categorical Features: {len(categorical_columns)}")

        if categorical_columns:

            print("\nCategorical Columns")
            print("-" * 70)

            for column in categorical_columns:
                print(column)

        else:

            print("\n✓ No categorical features found.")

        # ==========================================================
    # STEP 5: Validate Feature Consistency
    # ==========================================================

    def validate_feature_consistency(self) -> None:
        """
        Ensure all dataset splits contain identical features.
        """

        print("\n" + "=" * 70)
        print("FEATURE CONSISTENCY CHECK")
        print("=" * 70)

        train_columns = self.X_train.columns
        validation_columns = self.X_validation.columns
        test_columns = self.X_test.columns

        validation_match = train_columns.equals(validation_columns)
        test_match = train_columns.equals(test_columns)

        print(f"Training vs Validation : {validation_match}")
        print(f"Training vs Test       : {test_match}")

        if validation_match and test_match:
            print("\n✓ All dataset splits contain identical features.")

        else:
            raise ValueError(
                "Feature mismatch detected between dataset splits."
            )
        # ==========================================================
    # STEP 6: Save Processed Datasets
    # ==========================================================

    def save_processed_datasets(self) -> None:
        """
        Save the processed datasets for downstream machine learning tasks.
        """

        print("\n" + "=" * 70)
        print("SAVE PROCESSED DATASETS")
        print("=" * 70)

        train_processed = pd.concat(
            [self.X_train, self.y_train],
            axis=1,
        )

        validation_processed = pd.concat(
            [self.X_validation, self.y_validation],
            axis=1,
        )

        test_processed = pd.concat(
            [self.X_test, self.y_test],
            axis=1,
        )

        train_processed.to_csv(
            self.processed_train_path,
            index=False,
        )

        validation_processed.to_csv(
            self.processed_validation_path,
            index=False,
        )

        test_processed.to_csv(
            self.processed_test_path,
            index=False,
        )

        print("✓ Processed datasets saved successfully.\n")

        print(f"Training   : {self.processed_train_path}")
        print(f"Validation : {self.processed_validation_path}")
        print(f"Test       : {self.processed_test_path}")
    

    



    def run(self):
        """
        Execute the preprocessing pipeline.
        """

        self.load_datasets()

        self.separate_features_and_target()

        self.handle_missing_values()

        self.inspect_features()

        self.identify_feature_types()

        self.validate_feature_consistency()

        self.save_processed_datasets()


if __name__ == "__main__":

    preprocessing = Preprocessing()

    preprocessing.run()