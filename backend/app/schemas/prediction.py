from datetime import datetime

from pydantic import BaseModel


# ==========================================================
# Existing API Schemas
# ==========================================================

class PredictionBatchRequest(BaseModel):
    """
    Request used for predicting multiple matches.
    """

    match_ids: list[int]


class MatchPredictionResponse(BaseModel):
    """
    Prediction response for a single match in a batch.
    """

    match_id: int

    prediction: str

    prediction_code: int

    home_probability: float

    draw_probability: float

    away_probability: float


class PredictionDetail(BaseModel):
    """
    Detailed prediction stored in the database.
    """

    id: int

    match_id: int

    model_name: str

    prediction: str

    home_probability: float

    draw_probability: float

    away_probability: float

    predicted_at: datetime
    verification_status: str = 'legacy_unverified'

    class Config:

        from_attributes = True


class PredictionResponse(BaseModel):
    """
    Response returned after predicting a single match.
    """

    prediction: str

    prediction_code: int

    home_probability: float

    draw_probability: float

    away_probability: float


# ==========================================================
# New Prediction Service Schemas
# ==========================================================

class PredictionDatabaseResponse(BaseModel):
    """
    Prediction stored inside the database.
    """

    id: int

    match_id: int

    model_name: str

    prediction: str

    home_probability: float

    draw_probability: float

    away_probability: float

    predicted_at: datetime

    class Config:

        from_attributes = True


class PredictionListResponse(BaseModel):
    """
    List of predictions.
    """

    predictions: list[MatchPredictionResponse]


class PredictionRequest(BaseModel):
    """
    Request body used when predicting multiple matches.
    """

    match_ids: list[int]


class UpcomingPredictionRequest(BaseModel):
    """
    Predict upcoming matches.
    """

    days: int = 7


class CleanupPredictionRequest(BaseModel):
    """
    Delete old predictions.
    """

    days: int = 30
