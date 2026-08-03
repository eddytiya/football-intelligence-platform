from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.match_repository import MatchRepository
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.prediction import (
    PredictionResponse,
    PredictionDatabaseResponse,
    PredictionListResponse,
    PredictionRequest,
    UpcomingPredictionRequest,
    CleanupPredictionRequest,
)
from app.services.feature_engineering.team_analytics import TeamAnalytics
from app.services.prediction_service import PredictionService

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


def get_prediction_service(
    db: Session = Depends(get_db),
) -> PredictionService:
    """
    Create PredictionService with all dependencies.
    """

    match_repository = MatchRepository(db)

    prediction_repository = PredictionRepository(db)

    analytics = TeamAnalytics(
        match_repository
    )

    return PredictionService(
        prediction_repository=prediction_repository,
        match_repository=match_repository,
        team_analytics=analytics,
    )


@router.get(
    "/health",
)
def prediction_health():
    """
    Prediction API health check.
    """

    return {
        "status": "Prediction API Running"
    }


@router.post(
    "/{match_id}",
    response_model=PredictionResponse,
)
def predict_match(
    match_id: int,
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Generate prediction for a single match.
    """

    try:

        return prediction_service.predict_match(
            match_id=match_id,
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "/match/{match_id}",
    response_model=PredictionDatabaseResponse,
)
def get_prediction(
    match_id: int,
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Return a saved prediction for a match.
    """

    prediction = prediction_service.get_prediction(
        match_id
    )

    if prediction is None:

        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return prediction


@router.get(
    "/today",
)
def get_today_predictions(
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Return today's predictions.
    """

    return prediction_service.get_today_predictions()


@router.post(
    "/batch",
    response_model=PredictionListResponse,
)
def predict_multiple_matches(
    request: PredictionRequest,
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Predict multiple matches.
    """

    predictions = (
        prediction_service.predict_matches(
            match_ids=request.match_ids,
        )
    )

    return {
        "predictions": predictions
    }


@router.post(
    "/upcoming",
)
def predict_upcoming_matches(
    request: UpcomingPredictionRequest,
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Predict all upcoming matches.
    """

    return prediction_service.predict_upcoming_matches(
        days=request.days,
    )


@router.delete(
    "/cleanup",
)
def cleanup_predictions(
    request: CleanupPredictionRequest,
    prediction_service: PredictionService = Depends(
        get_prediction_service,
    ),
):
    """
    Delete old predictions.
    """

    deleted = (
        prediction_service.delete_old_predictions(
            days=request.days,
        )
    )

    return {
        "deleted_predictions": deleted
    }