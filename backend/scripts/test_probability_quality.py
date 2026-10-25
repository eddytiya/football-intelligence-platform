"""Numerical checks for the isolated probability experiment."""
import unittest

import numpy as np
from sklearn.metrics import log_loss

from experiment_probability_quality import (
    apply_recipe, best_weights, fit_temperature, temperature_scale, validate_probabilities,
)


class ProbabilityQualityTests(unittest.TestCase):
    def test_identity_and_argmax(self):
        p = np.array([[.1, .3, .6], [.7, .2, .1]])
        np.testing.assert_allclose(temperature_scale(p, 1), p)
        for temperature in (.25, 2, 4):
            adjusted = temperature_scale(p, temperature)
            validate_probabilities(adjusted)
            np.testing.assert_array_equal(adjusted.argmax(axis=1), p.argmax(axis=1))

    def test_calibration_reduces_overconfidence(self):
        p = np.tile([.98, .01, .01], (100, 1))
        y = np.array([0] * 50 + [1] * 25 + [2] * 25)
        temperature = fit_temperature(p, y)
        self.assertGreater(temperature, 1)
        self.assertLess(log_loss(y, temperature_scale(p, temperature)), log_loss(y, p))

    def test_grid_can_select_single_best_model(self):
        y = np.array([0, 1, 2])
        good = np.eye(3) * .8 + .2 / 3
        bad = np.full((3, 3), 1 / 3)
        p = np.stack([bad, good, bad])
        weights = best_weights(p, y)
        np.testing.assert_allclose(weights, [0, 1, 0])
        recipe = {"weights": weights, "temperatures": [1, 1, 1], "blend_temperature": 1}
        np.testing.assert_allclose(apply_recipe(p, recipe), good)

    def test_invalid_distributions_are_rejected(self):
        for p in (np.array([[.1, .1, .1]]), np.array([[np.nan, .5, .5]]), np.array([[-.2, .6, .6]])):
            with self.assertRaises(ValueError):
                validate_probabilities(p)
        with self.assertRaises(ValueError):
            temperature_scale(np.array([[.2, .3, .5]]), 0)


if __name__ == "__main__":
    unittest.main()
