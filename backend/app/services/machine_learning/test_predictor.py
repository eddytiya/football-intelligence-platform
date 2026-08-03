import pandas as pd

from app.core.paths import PROCESSED_DATA_DIR
from app.services.machine_learning.predictor import Predictor


print("=" * 70)
print("Football Intelligence Platform")
print("Machine Learning - Predictor Test")
print("=" * 70)

# ==========================================================
# Load Test Dataset
# ==========================================================

test_path = PROCESSED_DATA_DIR / "test_selected.csv"

print("\nLoading test dataset...")

test_df = pd.read_csv(test_path)

print("✓ Test dataset loaded")
print(f"Shape : {test_df.shape}")

# ==========================================================
# Prepare Features
# ==========================================================

target_column = "match_result"

X_test = test_df.drop(columns=target_column)

print("\nPreparing features...")
print(f"Matches : {len(X_test)}")

# ==========================================================
# Load Predictor
# ==========================================================

predictor = Predictor()

predictor.load_model()

# ==========================================================
# Predict First Match
# ==========================================================

print()
print("=" * 70)
print("FIRST MATCH PREDICTION")
print("=" * 70)

result = predictor.predict_match(
    X_test.iloc[[0]]
)

print(f"Prediction : {result['prediction']}")
print(f"Code       : {result['prediction_code']}")

print("\nProbabilities")
print("-" * 70)

for outcome, probability in result["probabilities"].items():
    print(f"{outcome:<10}: {probability:.4f}")

# ==========================================================
# Batch Prediction
# ==========================================================

print()
print("=" * 70)
print("FIRST 5 MATCHES")
print("=" * 70)

batch_results = predictor.predict_batch(
    X_test.head(5)
)

print(batch_results)