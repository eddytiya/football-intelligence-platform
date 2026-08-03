from app.db.session import SessionLocal
from app.services.machine_learning.prediction_service import PredictionService


def main():

    db = SessionLocal()

    service = PredictionService(db)

    print("=" * 70)
    print("Prediction Service Created Successfully")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    main()