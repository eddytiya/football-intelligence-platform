from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.schemas.prediction_evaluation import (
    PredictionAccuracyResponse,
    PredictionEvaluationDetail,
    PredictionEvaluationResponse,
)
from app.services.prediction.prediction_evaluation import (
    PredictionEvaluationService,
)

router = APIRouter(
    prefix="/evaluations",
    tags=["Prediction Evaluations"],
)


# ==========================================================
# Evaluate Prediction
# ==========================================================

@router.post(
    "/{prediction_id}",
    response_model=PredictionEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Evaluate a prediction after the match
    has finished.
    """

    service = PredictionEvaluationService(db)

    try:
        return service.evaluate_prediction(
            prediction_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ==========================================================
# Get Evaluation By Prediction
# ==========================================================

@router.get(
    "/prediction/{prediction_id}",
    response_model=PredictionEvaluationDetail,
)
def get_prediction_evaluation(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve evaluation for a prediction.
    """

    service = PredictionEvaluationService(db)

    evaluation = service.get_prediction_evaluation(
        prediction_id
    )

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found.",
        )

    return evaluation


# ==========================================================
# Get All Evaluations
# ==========================================================

@router.get(
    "",
    response_model=list[PredictionEvaluationDetail],
)
def get_all_evaluations(
    db: Session = Depends(get_db),
):
    """
    Retrieve all prediction evaluations.
    """

    service = PredictionEvaluationService(db)

    return service.get_all_evaluations()


# ==========================================================
# Get Accuracy
# ==========================================================

@router.get(
    "/accuracy",
    response_model=PredictionAccuracyResponse,
)
def get_accuracy(
    db: Session = Depends(get_db),
):
    """
    Retrieve overall prediction accuracy.
    """

    service = PredictionEvaluationService(db)

    return service.get_accuracy()


# ==========================================================
# Get Evaluation By ID
# ==========================================================

@router.get(
    "/{evaluation_id}",
    response_model=PredictionEvaluationDetail,
)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve an evaluation by ID.
    """

    service = PredictionEvaluationService(db)

    evaluation = service.get_evaluation(
        evaluation_id
    )

    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found.",
        )

    return evaluation


# ==========================================================
# Delete Evaluation
# ==========================================================

@router.delete(
    "/{evaluation_id}",
)
def delete_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a prediction evaluation.
    """

    service = PredictionEvaluationService(db)

    deleted = service.delete_evaluation(
        evaluation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found.",
        )

    return {
        "message": "Evaluation deleted successfully."
    }