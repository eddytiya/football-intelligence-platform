import pandas as pd

from app.services.machine_learning.predictor import Predictor


class ReorderedClassesModel:
    """Minimal estimator exposing probability columns in a non-default order."""

    classes_ = [2, 0, 1]

    def predict(self, features):
        return [2] * len(features)

    def predict_proba(self, features):
        return [[0.7, 0.2, 0.1]] * len(features)


def test_predict_match_maps_probabilities_using_model_classes():
    predictor = Predictor()
    predictor.model = ReorderedClassesModel()

    result = predictor.predict_match(pd.DataFrame({"feature": [1]}))

    assert result == {
        "prediction": "Home Win",
        "prediction_code": 2,
        "probabilities": {
            "Away Win": 0.2,
            "Draw": 0.1,
            "Home Win": 0.7,
        },
    }
