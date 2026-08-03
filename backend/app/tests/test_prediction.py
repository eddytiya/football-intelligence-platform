from app.db.session import SessionLocal
from app.services.machine_learning.prediction_service import PredictionService


def main():
    db = SessionLocal()

    service = PredictionService(db)

    result = service.predict_match(
        match_id=1,      # Replace with a valid match ID
    )

    print()
    print("=" * 70)
    print("Prediction Result")
    print("=" * 70)
    print(result)

    db.close()


if __name__ == "__main__":
    main()