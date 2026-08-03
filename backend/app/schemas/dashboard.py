from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class SummaryStatisticsResponse(BaseModel):
    """
    Dashboard summary statistics.
    """

    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    today_predictions: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class RecentPredictionResponse(BaseModel):
    """
    Recent prediction information.
    """

    match: str
    prediction: str
    actual_result: str | None = None
    correct: bool | None = None
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class UpcomingMatchResponse(BaseModel):
    """
    Upcoming match information.
    """

    home_team: str
    away_team: str
    competition: str
    utc_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelPerformanceResponse(BaseModel):
    """
    Model performance summary.
    """

    accuracy: float
    total_predictions: int

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """
    Complete dashboard response.
    """

    summary: SummaryStatisticsResponse
    recent_predictions: List[RecentPredictionResponse]
    upcoming_matches: List[UpcomingMatchResponse]
    model_performance: ModelPerformanceResponse

    model_config = ConfigDict(from_attributes=True)