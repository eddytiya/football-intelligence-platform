from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    log_loss,
)
import numpy as np


class Evaluator:
    """
    Evaluates machine learning classification models.
    """

    def __init__(self):
        """
        Initialize evaluator.
        """

        self.results = {}

    def evaluate(
        self,
        y_true,
        y_pred,
        y_probability=None,
    ):
        """
        Evaluate model predictions.

        Parameters
        ----------
        y_true : array-like
            Actual target values.

        y_pred : array-like
            Predicted target values.

        y_probability : array-like, optional
            Predicted class probabilities.

        Returns
        -------
        dict
            Dictionary containing evaluation metrics.
        """

        # ==========================================================
        # Basic Metrics
        # ==========================================================

        accuracy = accuracy_score(
            y_true,
            y_pred,
        )

        balanced_accuracy = balanced_accuracy_score(
            y_true,
            y_pred,
        )

        precision = precision_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0,
        )

        # ==========================================================
        # Confusion Matrix
        # ==========================================================

        cm = confusion_matrix(
            y_true,
            y_pred,
        )

        # ==========================================================
        # Classification Report
        # ==========================================================

        report = classification_report(
            y_true,
            y_pred,
            output_dict=True,
            zero_division=0,
        )

        # ==========================================================
        # Log Loss
        # ==========================================================

        loss = None
        brier = None
        calibration_gap = None

        if y_probability is not None:
            loss = log_loss(
                y_true,
                y_probability,
            )
            probabilities = np.asarray(y_probability, dtype=float)
            classes = np.unique(y_true)
            target = np.zeros_like(probabilities)
            for index, label in enumerate(classes):
                if index < target.shape[1]:
                    target[:, index] = (np.asarray(y_true) == label).astype(float)
            brier = float(np.mean(np.sum((probabilities - target) ** 2, axis=1)))
            confidence = probabilities.max(axis=1)
            correct = (np.asarray(y_pred) == np.asarray(y_true)).astype(float)
            bins = np.linspace(0, 1, 11)
            calibration_gap = 0.0
            for start, end in zip(bins[:-1], bins[1:]):
                mask = (confidence >= start) & (confidence < end if end < 1 else confidence <= end)
                if mask.any():
                    calibration_gap += abs(correct[mask].mean() - confidence[mask].mean()) * mask.mean()

        # ==========================================================
        # Store Results
        # ==========================================================

        self.results = {
            "accuracy": accuracy,
            "balanced_accuracy": balanced_accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "log_loss": loss,
            "multiclass_brier_score": brier,
            "expected_calibration_gap": calibration_gap,
            "confusion_matrix": cm,
            "classification_report": report,
        }

        return self.results

    def get_results(self):
        """
        Return evaluation results.
        """

        return self.results

    def reset(self):
        """
        Reset stored evaluation results.
        """

        self.results = {}

    def print_summary(self):
        """
        Print summary metrics.
        """

        if not self.results:
            print("No evaluation results available.")
            return

        print()
        print("=" * 70)
        print("MODEL EVALUATION SUMMARY")
        print("=" * 70)

        print(f"Accuracy            : {self.results['accuracy']:.4f}")
        print(f"Balanced Accuracy   : {self.results['balanced_accuracy']:.4f}")
        print(f"Precision           : {self.results['precision']:.4f}")
        print(f"Recall              : {self.results['recall']:.4f}")
        print(f"F1 Score            : {self.results['f1_score']:.4f}")

        if self.results["log_loss"] is not None:
            print(f"Log Loss            : {self.results['log_loss']:.4f}")
            print(f"Brier Score         : {self.results['multiclass_brier_score']:.4f}")
            print(f"Calibration Gap     : {self.results['expected_calibration_gap']:.4f}")

        print("=" * 70)

    def print_confusion_matrix(self):
        """
        Print confusion matrix.
        """

        if not self.results:
            print("No evaluation results available.")
            return

        print()
        print("=" * 70)
        print("CONFUSION MATRIX")
        print("=" * 70)

        print(self.results["confusion_matrix"])

    def print_classification_report(self):
        """
        Print classification report.
        """

        if not self.results:
            print("No evaluation results available.")
            return

        print()
        print("=" * 70)
        print("CLASSIFICATION REPORT")
        print("=" * 70)

        report = self.results["classification_report"]

        for class_name, metrics in report.items():

            if isinstance(metrics, dict):

                print(f"\n{class_name}")

                for metric_name, value in metrics.items():

                    print(f"    {metric_name:<12}: {value:.4f}")

            else:

                print(f"{class_name:<20}: {metrics:.4f}")
