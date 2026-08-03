from app.services.machine_learning.trainer import Trainer
from app.services.machine_learning.evaluator import Evaluator

# ---------------------------------------------------------
# Load datasets
# ---------------------------------------------------------

trainer = Trainer()
trainer.setup()

# ---------------------------------------------------------
# Train one model
# ---------------------------------------------------------

trainer.train_model("random_forest")

# ---------------------------------------------------------
# Predict validation set
# ---------------------------------------------------------

predictions = trainer.predict_validation()

# ---------------------------------------------------------
# Evaluate
# ---------------------------------------------------------

evaluator = Evaluator()

results = evaluator.evaluate(
    trainer.y_validation,
    predictions,
)

# ---------------------------------------------------------
# Print Results
# ---------------------------------------------------------

evaluator.print_summary()

evaluator.print_confusion_matrix()

evaluator.print_classification_report()