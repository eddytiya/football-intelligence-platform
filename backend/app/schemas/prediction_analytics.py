from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class OverallStatisticsResponse(BaseModel):
    """
    Overall prediction statistics.
    """

    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class AverageProbabilitiesResponse(BaseModel):
    """
    Average prediction probabilities.
    """

    home_probability: float
    draw_probability: float
    away_probability: float

    model_config = ConfigDict(from_attributes=True)


class DailyStatisticsResponse(BaseModel):
    """
    Daily prediction statistics.
    """

    date: str
    predictions: int

    model_config = ConfigDict(from_attributes=True)


class DashboardStatisticsResponse(BaseModel):
    """
    Complete analytics dashboard.
    """

    overall: OverallStatisticsResponse
    distribution: Dict[str, int]
    average_probabilities: AverageProbabilitiesResponse
    daily_statistics: List[DailyStatisticsResponse]

    model_config = ConfigDict(from_attributes=True)