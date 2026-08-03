from app.services.machine_learning.evaluator import Evaluator
from app.services.machine_learning.model_manager import ModelManager
from app.services.machine_learning.trainer import Trainer
from app.services.machine_learning.hyperparameter_tuner import HyperparameterTuner

class TrainingPipeline:
    """
    Coordinates the entire machine learning workflow.

    Workflow
    --------
    Load datasets
        ↓
    Train model
        ↓
    Predict validation
        ↓
    Evaluate
        ↓
    Save model
        ↓
    Save metadata
    """

    def __init__(self):
        self.trainer = Trainer()
        self.evaluator = Evaluator()
        self.model_manager = ModelManager()

    def run(
        self,
        model_name: str,
    ):
        """
        Execute the complete training pipeline.

        Parameters
        ----------
        model_name : str
            Model to train.

        Returns
        -------
        dict
            Trained model, evaluation metrics, and metadata.
        """

        print()
        print("=" * 70)
        print(f"TRAINING PIPELINE : {model_name}")
        print("=" * 70)

        # ---------------------------------------------------------
        # Load datasets
        # ---------------------------------------------------------

        self.trainer.setup()

        # ---------------------------------------------------------
        # Train model
        # ---------------------------------------------------------

        self.trainer.train_model(model_name)

        # ---------------------------------------------------------
        # Predict validation
        # ---------------------------------------------------------

        predictions = self.trainer.predict_validation()

        # ---------------------------------------------------------
        # Evaluate
        # ---------------------------------------------------------

        results = self.evaluator.evaluate(
            self.trainer.y_validation,
            predictions,
            self.trainer.model.predict_proba(self.trainer.X_validation),
        )

        self.evaluator.print_summary()

        # ---------------------------------------------------------
        # Save model
        # ---------------------------------------------------------

        self.model_manager.save_model(
            model_name,
            self.trainer.model,
        )

        # A single training run produces a named candidate, not necessarily
        # the best model. `ModelComparison` promotes the ranked winner after
        # evaluating every candidate; overwriting best_model here made the
        # production artifact depend on whichever model happened to run last.

        # ---------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------

        metadata = {
            "model_name": model_name,
            "accuracy": results["accuracy"],
            "balanced_accuracy": results["balanced_accuracy"],
            "precision": results["precision"],
            "recall": results["recall"],
            "f1_score": results["f1_score"],
            "log_loss": results["log_loss"],
            "multiclass_brier_score": results["multiclass_brier_score"],
            "expected_calibration_gap": results["expected_calibration_gap"],
            "training_samples": len(self.trainer.y_train),
            "validation_samples": len(self.trainer.y_validation),
            "number_of_features": self.trainer.X_train.shape[1],
        }

        self.model_manager.save_metadata(
            model_name,
            metadata,
        )

        print()
        print("=" * 70)
        print("PIPELINE COMPLETED")
        print("=" * 70)

        return {
            "model": self.trainer.model,
            "metrics": results,
            "metadata": metadata,
        }

if __name__ == "__main__":

    print("=" * 70)
    print("Football Intelligence Platform")
    print("Machine Learning - Training Pipeline")
    print("=" * 70)

    pipeline = TrainingPipeline()

    result = pipeline.run(
        model_name="catboost",
    )

    print()
    print("=" * 70)
    print("Training Finished")
    print("=" * 70)

    print("Metrics")

    for metric, value in result["metrics"].items():
        print(f"{metric}: {value}")
