from app.services.machine_learning.model_factory import ModelFactory

models = [
    "logistic_regression",
    "random_forest",
    "extra_trees",
    "gradient_boosting",
    "xgboost",
    "lightgbm",
    "catboost",
]

print("=" * 60)
print("Testing Model Factory")
print("=" * 60)

for model_name in models:
    model = ModelFactory.create(model_name)
    print(f"{model_name:<25} -> {type(model).__name__}")

print("=" * 60)
print("All models created successfully.")
print("=" * 60)