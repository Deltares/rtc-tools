import logging

import numpy as np

from ..test_case import TestCase
from .test_modelica_mixin import ModelAlgebraic, ModelMixedInteger

logger = logging.getLogger("rtctools")
logger.setLevel(logging.DEBUG)


class ModelCLP(ModelAlgebraic):
    def solver_options(self):
        options = super().solver_options()
        options["solver"] = "clp"
        options["casadi_solver"] = "qpsol"
        return options


class ModelHiGHS_alg(ModelAlgebraic):
    def solver_options(self):
        options = super().solver_options()
        options["solver"] = "highs"
        options["casadi_solver"] = "qpsol"
        return options


class ModelHiGHS_MIP(ModelMixedInteger):
    def solver_options(self):
        options = super().solver_options()
        options["solver"] = "highs"
        options["casadi_solver"] = "qpsol"
        return options


class TestSolverCLP(TestCase):
    def setUp(self):
        self.problem = ModelCLP()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6

    def test_solver_clp(self):
        self.assertAlmostEqual(
            self.results["y"] + self.results["u"],
            np.ones(len(self.problem.times())) * 1.0,
            self.tolerance,
        )


class TestSolverHiGHS_alg(TestCase):
    def setUp(self):
        self.problem = ModelHiGHS_alg()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6

    def test_solver_HiGHS(self):
        self.assertAlmostEqual(
            self.results["y"] + self.results["u"],
            np.ones(len(self.problem.times())) * 1.0,
            self.tolerance,
        )


class TestSolverHiGHS_MIP(TestCase):
    def setUp(self):
        self.problem = ModelHiGHS_MIP()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6

    def test_booleans(self):
        self.assertAlmostEqual(self.results["choice"], np.zeros(21, dtype=bool), self.tolerance)
        self.assertAlmostEqual(
            self.results["other_choice"], np.ones(21, dtype=bool), self.tolerance
        )
        self.assertAlmostEqual(self.results["y"], -1 * np.ones(21, dtype=bool), self.tolerance)
