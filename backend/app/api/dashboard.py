from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardResponse,
    ModelPerformanceResponse,
    RecentPredictionResponse,
    SummaryStatisticsResponse,
    UpcomingMatchResponse,
)
from app.services.dashboard.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=SummaryStatisticsResponse,
)
def get_summary_statistics(
    db: Session = Depends(get_db),
):
    """
    Get dashboard summary statistics.
    """
    service = DashboardService(db)
    return service.get_summary_statistics()


@router.get(
    "/recent-predictions",
    response_model=list[RecentPredictionResponse],
)
def get_recent_predictions(
    db: Session = Depends(get_db),
):
    """
    Get recent predictions.
    """
    service = DashboardService(db)
    return service.get_recent_predictions()


@router.get(
    "/upcoming-matches",
    response_model=list[UpcomingMatchResponse],
)
def get_upcoming_matches(
    db: Session = Depends(get_db),
):
    """
    Get upcoming matches.
    """
    service = DashboardService(db)
    return service.get_upcoming_matches()


@router.get(
    "/model-performance",
    response_model=ModelPerformanceResponse,
)
def get_model_performance(
    db: Session = Depends(get_db),
):
    """
    Get model performance.
    """
    service = DashboardService(db)
    return service.get_model_performance()


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
):
    """
    Get complete dashboard.
    """
    service = DashboardService(db)
    return service.get_dashboard()


@router.get("/command-centre")
def get_command_centre(db: Session = Depends(get_db)):
    """Live dashboard payload built solely from currently stored football data."""
    return DashboardService(db).get_command_centre()
