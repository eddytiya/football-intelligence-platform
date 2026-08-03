from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prediction import (
    PredictionBatchRequest,
    MatchPredictionResponse,
    PredictionDetail,
    PredictionResponse,
)
from app.services.prediction.prediction_service import PredictionService
from app.services.machine_learning.historical_match_model import HistoricalMatchModel
from app.repositories.match_repository import MatchRepository

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


@lru_cache(maxsize=1)
def get_historical_model() -> HistoricalMatchModel:
    """Load the CSV-trained artifact once per API process."""
    return HistoricalMatchModel.load()


@router.get("/historical/match/{match_id}")
def get_historical_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    """Return the historical-model probabilities for one scheduled match."""
    match = MatchRepository(db).get_match_by_id(match_id)

    if match is None:
        raise HTTPException(status_code=404, detail="Match not found.")

    if match.competition is None or match.home_team is None or match.away_team is None:
        raise HTTPException(status_code=422, detail="Match is missing team or competition data.")

    try:
        prediction = get_historical_model().predict_fixture(
            league=match.competition.code,
            home_team=match.home_team.name,
            away_team=match.away_team.name,
            match_date=match.utc_date,
        )
        prediction["match_id"] = match.id
        return prediction
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Historical model has not been trained.") from exc

# ==========================================================
# Batch Predictions
# ==========================================================


@router.post(
    "/batch",
    response_model=list[MatchPredictionResponse],
)
def predict_matches(
    request: PredictionBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Generate predictions for multiple matches.
    """

    prediction_service = PredictionService(db)

    return prediction_service.predict_matches(
        request.match_ids
    )

def predict_upcoming_matches(
        self,
        days: int = 7,
    ):
        """
        Generate predictions for all upcoming matches.
        """

        print()
        print("=" * 70)
        print("Predict Upcoming Matches")
        print("=" * 70)

        matches = self.repository.get_upcoming_matches()

        print(
            f"Upcoming Matches : {len(matches)}"
        )

        predictions = []

        for match in matches:

            result = self.predict_match(
                match.id
            )

            predictions.append(
                {
                    "match_id": match.id,
                    "prediction": result["prediction"],
                    "prediction_code": result["prediction_code"],
                    "home_probability": result["probabilities"]["Home Win"],
                    "draw_probability": result["probabilities"]["Draw"],
                    "away_probability": result["probabilities"]["Away Win"],
                }
            )

        return predictions
# ==========================================================
# Generate Prediction
# ==========================================================


@router.post(
    "/match/{match_id}",
    response_model=PredictionResponse,
)
def predict_match(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate and save a prediction for a football match.
    """

    prediction_service = PredictionService(db)

    try:
        prediction = prediction_service.predict_match(match_id)

        return PredictionResponse(
            prediction=prediction["prediction"],
            prediction_code=prediction["prediction_code"],
            home_probability=prediction["probabilities"]["Home Win"],
            draw_probability=prediction["probabilities"]["Draw"],
            away_probability=prediction["probabilities"]["Away Win"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ==========================================================
# Upcoming Match Predictions
# ==========================================================


@router.get(
    "/upcoming",
)
def get_upcoming_predictions(
    db: Session = Depends(get_db),
):
    """
    Generate predictions for all upcoming matches.
    """

    prediction_service = PredictionService(db)

    return prediction_service.predict_upcoming_matches()


# ==========================================================
# Today's Predictions
# ==========================================================


@router.get(
    "/today",
    response_model=list[PredictionDetail],
)
def get_todays_predictions(
    db: Session = Depends(get_db),
):
    """
    Return today's predictions.
    """

    prediction_service = PredictionService(db)

    return prediction_service.get_todays_predictions()


# ==========================================================
# Prediction By Match
# ==========================================================


@router.get(
    "/match/{match_id}",
    response_model=PredictionDetail,
)
def get_match_prediction(
    match_id: int,
    db: Session = Depends(get_db),
):
    """
    Return prediction for a specific match.
    """

    prediction_service = PredictionService(db)

    prediction = prediction_service.get_match_prediction(
        match_id
    )

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return prediction


# ==========================================================
# Predictions By Competition
# ==========================================================


@router.get(
    "/competition/{competition_id}",
    response_model=list[PredictionDetail],
)
def get_competition_predictions(
    competition_id: int,
    db: Session = Depends(get_db),
):
    """
    Return predictions for a competition.
    """

    prediction_service = PredictionService(db)

    return prediction_service.get_competition_predictions(
        competition_id
    )


# ==========================================================
# Prediction By Prediction ID
# ==========================================================


@router.get(
    "/{prediction_id}",
    response_model=PredictionDetail,
)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Return prediction by prediction ID.
    """

    prediction_service = PredictionService(db)

    prediction = prediction_service.get_prediction(
        prediction_id
    )

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return prediction


# ==========================================================
# Delete Prediction
# ==========================================================


@router.delete(
    "/{prediction_id}",
)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a prediction.
    """

    prediction_service = PredictionService(db)

    deleted = prediction_service.delete_prediction(
        prediction_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    return {
        "message": "Prediction deleted successfully."
    }
