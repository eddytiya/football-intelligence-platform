from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
)

from sklearn.linear_model import LogisticRegression

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

import json

from app.core.paths import REPORTS_DIR


class ModelFactory:
    """
    Factory responsible for creating machine learning models.

    This class centralizes the creation of all supported
    classifiers used throughout the Football Intelligence Platform.
    """

    @staticmethod
    def load_tuned_parameters(
        model_name: str,
    ) -> dict:
        """
        Load tuned hyperparameters if available.
        """

        parameter_file = (
            REPORTS_DIR /
            f"{model_name}_best_parameters.json"
        )

        if parameter_file.exists():

            with open(parameter_file, "r") as file:
                return json.load(file)

        return {}

    @staticmethod
    def create(model_name: str, **kwargs):
        """
        Create and return a machine learning model.

        Parameters
        ----------
        model_name : str
            Name of the machine learning model.

        kwargs : dict
            Optional parameters that override the default settings.

        Returns
        -------
        sklearn-compatible classifier
            An initialized machine learning model.

        Raises
        ------
        ValueError
            If the requested model is not supported.
        """

        # Normalize model name
        model_name = model_name.lower()

        # ---------------------------------------------------------
        # Load tuned parameters
        # ---------------------------------------------------------

        tuned_parameters = ModelFactory.load_tuned_parameters(
            model_name
        )

        # Explicit parameters passed to create()
        # take precedence over tuned parameters.
        tuned_parameters.update(kwargs)

        # ---------------------------------------------------------
        # Logistic Regression
        # ---------------------------------------------------------
        if model_name == "logistic_regression":

            params = {
                "max_iter": 1000,
                "random_state": 42,
            }

            params.update(tuned_parameters)

            return LogisticRegression(**params)

        # ---------------------------------------------------------
        # Random Forest
        # ---------------------------------------------------------
        if model_name == "random_forest":

            params = {
                "n_estimators": 300,
                "random_state": 42,
                "n_jobs": -1,
            }

            params.update(tuned_parameters)

            return RandomForestClassifier(**params)

        # ---------------------------------------------------------
        # Extra Trees
        # ---------------------------------------------------------
        if model_name == "extra_trees":

            params = {
                "n_estimators": 300,
                "random_state": 42,
                "n_jobs": -1,
            }

            params.update(tuned_parameters)

            return ExtraTreesClassifier(**params)

        # ---------------------------------------------------------
        # Gradient Boosting
        # ---------------------------------------------------------
        if model_name == "gradient_boosting":

            params = {
                "random_state": 42,
            }

            params.update(tuned_parameters)

            return GradientBoostingClassifier(**params)

        # ---------------------------------------------------------
        # XGBoost
        # ---------------------------------------------------------
        if model_name == "xgboost":

            params = {
                "n_estimators": 300,
                "learning_rate": 0.05,
                "max_depth": 6,
                "objective": "multi:softprob",
                "eval_metric": "mlogloss",
                "random_state": 42,
                "n_jobs": -1,
            }

            params.update(tuned_parameters)

            return XGBClassifier(**params)

        # ---------------------------------------------------------
        # LightGBM
        # ---------------------------------------------------------
        if model_name == "lightgbm":

            params = {
                "n_estimators": 300,
                "learning_rate": 0.05,
                "random_state": 42,
                "n_jobs": -1,
            }

            params.update(tuned_parameters)

            return LGBMClassifier(**params)

        # ---------------------------------------------------------
        # CatBoost
        # ---------------------------------------------------------
        if model_name == "catboost":

            params = {
                "iterations": 300,
                "learning_rate": 0.05,
                "random_state": 42,
                "verbose": False,
            }

            params.update(tuned_parameters)

            return CatBoostClassifier(**params)

        # ---------------------------------------------------------
        # Unsupported Model
        # ---------------------------------------------------------
        raise ValueError(f"Unsupported model: {model_name}")