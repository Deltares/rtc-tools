import logging
import unittest

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.DEBUG)


class Model(ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self, inline_delay_expressions=False):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="ModelDelay",
            model_folder=data_path(),
        )
        self.inline_delay_expressions = inline_delay_expressions

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class ModelNoHistory(Model):
    def history(self, ensemble_member):
        return {}


class ModelPartialHistory(Model):
    def history(self, ensemble_member):
        history = super().history(ensemble_member)
        history["x"] = Timeseries(np.array([-0.2, -0.1, 0.0]), np.array([0.7, 0.9, 1.1]))
        return history


class ModelCompleteHistory(Model):
    def history(self, ensemble_member):
        history = super().history(ensemble_member)
        history["x"] = Timeseries(np.array([-0.2, -0.1, 0.0]), np.array([0.7, 0.9, 1.1]))
        history["w"] = Timeseries(np.array([-0.1, 0.0]), np.array([0.9, np.nan]))
        return history


class TestDelayHistoryWarnings(TestCase, unittest.TestCase):
    def test_no_history(self):
        # Test default mode
        problem = ModelNoHistory(inline_delay_expressions=False)
        with self.assertLogs(logger, level="WARN") as cm:
            problem.optimize()
            self.assertEqual(
                cm.output,
                [
                    "WARNING:rtctools:Incomplete history for delayed expression x. "
                    "Extrapolating t0 value backwards in time.",
                    "WARNING:rtctools:Incomplete history for delayed expression w. "
                    "Extrapolating t0 value backwards in time.",
                ],
            )
        results = problem.extract_results()

        # Test inline mode
        problem_inline = ModelNoHistory(inline_delay_expressions=True)
        with self.assertLogs(logger, level="WARN") as cm:
            problem_inline.optimize()
            self.assertEqual(
                cm.output,
                [
                    "WARNING:rtctools:Incomplete history for delayed expression x. "
                    "Extrapolating t0 value backwards in time.",
                    "WARNING:rtctools:Incomplete history for delayed expression w. "
                    "Extrapolating t0 value backwards in time.",
                ],
            )
        results_inline = problem_inline.extract_results()

        # Check that the results align
        self.assertAlmostEqual(results["x"], results_inline["x"], 1e-6)
        self.assertAlmostEqual(results["w"], results_inline["w"], 1e-6)

        # Check that the inline results has fewer constraints
        self.assertLess(
            len(problem_inline.transcribed_problem["lbg"]), len(problem.transcribed_problem["lbg"])
        )

    def test_partial_history(self):
        problem = ModelPartialHistory()
        with self.assertLogs(logger, level="WARN") as cm:
            problem.optimize()
            self.assertEqual(
                cm.output,
                [
                    "WARNING:rtctools:Incomplete history for delayed expression w. "
                    "Extrapolating t0 value backwards in time."
                ],
            )

    def test_complete_history(self):
        problem = ModelCompleteHistory()
        with self.assertLogs(logger, level="WARN") as cm:
            problem.optimize()
            self.assertEqual(cm.output, [])
            # if no log message occurs, assertLogs will throw an AssertionError
            logger.warning("All is well")
