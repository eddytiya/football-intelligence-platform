from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionEvaluationResponse(BaseModel):
    """
    Response returned after evaluating
    a prediction.
    """

    id: int
    prediction_id: int
    actual_result: str
    correct: bool
    evaluated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PredictionEvaluationDetail(BaseModel):
    """
    Detailed prediction evaluation.
    """

    id: int
    prediction_id: int
    actual_result: str
    correct: bool
    evaluated_at: datetime
    verification_status: str = 'legacy_unverified'

    model_config = ConfigDict(
        from_attributes=True,
    )


class PredictionAccuracyResponse(BaseModel):
    """
    Overall prediction accuracy statistics.
    """

    accuracy: float
    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
