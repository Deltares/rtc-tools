import logging
import os

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)


class Model(CSVMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self, **kwargs):
        kwargs["model_name"] = kwargs.get("model_name", "Model")
        kwargs["input_folder"] = kwargs.get("input_folder", data_path())
        kwargs["output_folder"] = kwargs.get("output_folder", data_path())
        kwargs["model_folder"] = kwargs.get("model_folder", data_path())
        super().__init__(**kwargs)

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times()[-1])
        f = xf**2
        return f

    def constraints(self, ensemble_member):
        # No additional constraints
        return []

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class ModelEnsemble(Model):
    csv_ensemble_mode = True

    def __init__(self, io_folder):
        super().__init__(
            input_folder=io_folder,
            output_folder=io_folder,
            model_name="Model",
            model_folder=data_path(),
            lookup_tables=[],
        )


class TestCSVMixin(TestCase):
    def setUp(self):
        self.problem = Model()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6

    def test_parameter(self):
        params = self.problem.parameters(0)
        self.assertEqual(params["k"], 1.01)

    def test_initial_state(self):
        history = self.problem.history(0)
        self.assertAlmostEqual(history["x"].values[-1], 1.02, self.tolerance)

    def test_objective_value(self):
        objective_value_tol = 1e-6
        self.assertTrue(abs(self.problem.objective_value) < objective_value_tol)

    def test_output(self):
        self.assertAlmostEqual(
            self.results["x"][:] ** 2 + np.sin(self.problem.times()),
            self.results["z"][:],
            self.tolerance,
        )

    def test_algebraic(self):
        self.assertAlmostEqual(
            self.results["y"] + self.results["x"],
            np.ones(len(self.problem.times())) * 3.0,
            self.tolerance,
        )

    def test_bounds(self):
        self.assertAlmostGreaterThan(self.results["u"], -2, self.tolerance)
        self.assertAlmostLessThan(self.results["u"], 2, self.tolerance)

    def test_interpolate(self):
        for v in ["x", "y", "u"]:
            for i in [0, int(len(self.problem.times()) / 2), -1]:
                a = self.problem.interpolate(
                    self.problem.times()[i],
                    self.problem.times(),
                    self.results[v],
                    0.0,
                    0.0,
                )
                b = self.results[v][i]
                self.assertAlmostEqual(a, b, self.tolerance)


class TestCSVMixinEnsemble(TestCase):
    def setUp(self):
        self.problem = ModelEnsemble(data_path())
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_objective_value(self):
        objective_value_tol = 1e-6
        self.assertTrue(abs(self.problem.objective_value) < objective_value_tol)


class TestCSVMixinOneMemberEnsemble(TestCase):
    def setUp(self):
        self.problem = ModelEnsemble(os.path.join(data_path(), "one-member-ensemble"))
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_objective_value(self):
        objective_value_tol = 1e-6
        self.assertTrue(abs(self.problem.objective_value) < objective_value_tol)
