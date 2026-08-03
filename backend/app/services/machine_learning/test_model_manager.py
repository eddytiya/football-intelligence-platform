from sklearn.ensemble import RandomForestClassifier

from app.services.machine_learning.model_manager import ModelManager


manager = ModelManager()

print("=" * 70)
print("MODEL MANAGER TEST")
print("=" * 70)

# ==========================================================
# Create Dummy Model
# ==========================================================

model = RandomForestClassifier()

# ==========================================================
# Save Model
# ==========================================================

manager.save_model(
    "random_forest",
    model,
)

# ==========================================================
# Save Metadata
# ==========================================================

metadata = {
    "algorithm": "Random Forest",
    "accuracy": 0.85,
    "balanced_accuracy": 0.82,
    "precision": 0.84,
    "recall": 0.83,
    "f1_score": 0.83,
}

manager.save_metadata(
    "random_forest",
    metadata,
)

# ==========================================================
# Check Existence
# ==========================================================

print()
print("Model Exists    :", manager.model_exists("random_forest"))
print("Metadata Exists :", manager.metadata_exists("random_forest"))

# ==========================================================
# List Models
# ==========================================================

print()
print("Saved Models:")
print(manager.list_models())

# ==========================================================
# Load Model
# ==========================================================

loaded_model = manager.load_model("random_forest")

print()
print("Loaded Model:")
print(type(loaded_model).__name__)

# ==========================================================
# Load Metadata
# ==========================================================

loaded_metadata = manager.load_metadata("random_forest")

print()
print("Loaded Metadata:")

for key, value in loaded_metadata.items():
    print(f"{key}: {value}")

# ==========================================================
# Save Best Model
# ==========================================================

manager.save_best_model(model)

# ==========================================================
# Load Best Model
# ==========================================================

best_model = manager.load_best_model()

print()
print("Best Model:")
print(type(best_model).__name__)

print()
print("=" * 70)
print("MODEL MANAGER TEST COMPLETED")
print("=" * 70)