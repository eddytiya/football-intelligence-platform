import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib

from app.core.paths import REPORTS_DIR, TRAINED_MODELS_DIR


class ModelManager:
    """
    Handles saving and loading trained machine learning models.

    Responsibilities
    ----------------
    - Save trained models
    - Load trained models
    - Save metadata
    - Load metadata
    - Save best model
    - Check if a model exists
    - List all saved models
    """

    def __init__(self):
        """
        Initialize model manager.
        """

        self.model_directory = TRAINED_MODELS_DIR
        self.reports_dir = REPORTS_DIR

        self.model_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.reports_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==========================================================
    # Internal Helpers
    # ==========================================================

    def _model_path(
        self,
        model_name: str,
    ) -> Path:
        """
        Return model file path.
        """

        return self.model_directory / f"{model_name}.joblib"

    def _metadata_path(
        self,
        model_name: str,
    ) -> Path:
        """
        Return metadata file path.
        """

        return self.model_directory / f"{model_name}_metadata.json"

    # ==========================================================
    # Model Operations
    # ==========================================================

    def save_model(
        self,
        model_name: str,
        model: Any,
    ) -> Path:
        """
        Save a trained model.

        Parameters
        ----------
        model_name : str
            Name of the model.

        model : Any
            Trained machine learning model.

        Returns
        -------
        Path
            Saved model path.
        """

        model_path = self._model_path(model_name)

        joblib.dump(
            model,
            model_path,
        )

        print(f"✓ Model saved: {model_path.name}")

        return model_path

    def load_model(
        self,
        model_name: str,
    ) -> Any:
        """
        Load a saved model.

        Parameters
        ----------
        model_name : str
            Name of the model.

        Returns
        -------
        Any
            Loaded model.
        """

        model_path = self._model_path(model_name)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model '{model_name}' does not exist."
            )

        model = joblib.load(model_path)

        print(f"✓ Model loaded: {model_path.name}")

        return model

    # ==========================================================
    # Metadata Operations
    # ==========================================================

    def save_metadata(
        self,
        model_name: str,
        metadata: dict,
    ) -> Path:
        """
        Save model metadata.

        Parameters
        ----------
        model_name : str
            Name of the model.

        metadata : dict
            Metadata dictionary.

        Returns
        -------
        Path
            Metadata file path.
        """

        metadata_path = self._metadata_path(model_name)

        metadata["saved_at"] = datetime.now().isoformat()

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                indent=4,
            )

        print(f"✓ Metadata saved: {metadata_path.name}")

        return metadata_path

    def load_metadata(
        self,
        model_name: str,
    ) -> dict:
        """
        Load model metadata.

        Parameters
        ----------
        model_name : str
            Name of the model.

        Returns
        -------
        dict
            Metadata dictionary.
        """

        metadata_path = self._metadata_path(model_name)

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata for '{model_name}' does not exist."
            )

        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        print(f"✓ Metadata loaded: {metadata_path.name}")

        return metadata

    # ==========================================================
    # Utility Methods
    # ==========================================================

    def model_exists(
        self,
        model_name: str,
    ) -> bool:
        """
        Check whether a model exists.
        """

        return self._model_path(model_name).exists()

    def metadata_exists(
        self,
        model_name: str,
    ) -> bool:
        """
        Check whether metadata exists.
        """

        return self._metadata_path(model_name).exists()

    def list_models(self) -> list[str]:
        """
        Return all saved model names.
        """

        models = []

        for file in self.model_directory.glob("*.joblib"):
            if file.name != "best_model.joblib":
                models.append(file.stem)

        models.sort()

        return models

    # ==========================================================
    # Best Model
    # ==========================================================

    def save_best_model(
        self,
        model: Any,
    ) -> Path:
        """
        Save the best performing model.

        Parameters
        ----------
        model : Any
            Trained model.

        Returns
        -------
        Path
            Saved file path.
        """

        best_model_path = self.model_directory / "best_model.joblib"

        joblib.dump(
            model,
            best_model_path,
        )

        print("✓ Best model updated")

        return best_model_path

    def load_best_model(self) -> Any:
        """
        Load the best model.

        Returns
        -------
        Any
            Loaded best model.
        """

        best_model_path = self.model_directory / "best_model.joblib"

        if not best_model_path.exists():
            raise FileNotFoundError(
                "Best model does not exist."
            )

        print("✓ Best model loaded")

        return joblib.load(best_model_path)

    def save_leaderboard(self, leaderboard):
        """
        Save the model leaderboard as a CSV file.
        """

        file_path = self.reports_dir / "model_leaderboard.csv"

        leaderboard.to_csv(file_path, index=False)

        print(f"✓ Leaderboard saved: {file_path.name}")


    def get_best_model_name(self, leaderboard):
        """
        Return the top-ranked model name.
        """

        return leaderboard.iloc[0]["model"]