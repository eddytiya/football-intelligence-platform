from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prediction_analytics import (
    DashboardStatisticsResponse,
)
from app.services.prediction_analytics import (
    PredictionAnalyticsService,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Prediction Analytics"],
)


@router.get("/overall")
def get_overall_statistics(
    db: Session = Depends(get_db),
):
    """
    Get overall prediction statistics.
    """
    service = PredictionAnalyticsService(db)

    return service.get_overall_statistics()


@router.get("/distribution")
def get_prediction_distribution(
    db: Session = Depends(get_db),
):
    """
    Get prediction distribution.
    """
    service = PredictionAnalyticsService(db)

    return service.get_prediction_distribution()


@router.get("/probabilities")
def get_average_probabilities(
    db: Session = Depends(get_db),
):
    """
    Get average prediction probabilities.
    """
    service = PredictionAnalyticsService(db)

    return service.get_average_probabilities()


@router.get("/daily")
def get_daily_statistics(
    db: Session = Depends(get_db),
):
    """
    Get daily prediction statistics.
    """
    service = PredictionAnalyticsService(db)

    return service.get_daily_statistics()


@router.get(
    "/dashboard",
    response_model=DashboardStatisticsResponse,
)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
):
    """
    Get complete analytics dashboard.
    """
    service = PredictionAnalyticsService(db)

    return service.get_dashboard_statistics()