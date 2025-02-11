import logging
import unittest

import numpy as np
from test_case import TestCase

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.DEBUG)


class Model(ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="ModelDelay",
            model_folder=data_path(),
        )

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
        problem = ModelNoHistory()
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
