import logging

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.planning_mixin import PlanningMixin
from rtctools.optimization.timeseries import Timeseries

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.DEBUG)


class Model(PlanningMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    planning_variables = ["u"]

    def __init__(self):
        super().__init__(model_name="ModelWithInitial", model_folder=data_path())

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    def parameters(self, ensemble_member):
        parameters = super().parameters(ensemble_member)
        parameters["u_max"] = 2.0
        return parameters

    def pre(self):
        # Do nothing
        pass

    @property
    def ensemble_size(self):
        return 3

    def constant_inputs(self, ensemble_member):
        # Constant inputs
        if ensemble_member == 0:
            return {"constant_input": Timeseries(self.times(), np.linspace(1.0, 0.0, 21))}
        elif ensemble_member == 1:
            return {"constant_input": Timeseries(self.times(), np.linspace(0.99, 0.5, 21))}
        else:
            return {"constant_input": Timeseries(self.times(), np.linspace(0.98, 1.0, 21))}

    def bounds(self):
        # Variable bounds
        return {"u": (-2.0, 2.0)}

    def seed(self, ensemble_member):
        # No particular seeding
        return {}

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2

    def constraints(self, ensemble_member):
        # No additional constraints
        return []

    def post(self):
        # Do
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class TestPlanningMixin(TestCase):
    def setUp(self):
        self.problem = Model()
        self.problem.optimize()
        self.results = [
            self.problem.extract_results(ensemble_member)
            for ensemble_member in range(self.problem.ensemble_size)
        ]

    def test_planning_variables(self):
        self.assertTrue(np.all(self.results[0]["u"] == self.results[1]["u"]))
        self.assertTrue(np.all(self.results[1]["u"] == self.results[2]["u"]))

    def test_other_variables(self):
        self.assertTrue(np.any(self.results[0]["x"] != self.results[1]["x"]))
        self.assertTrue(np.any(self.results[1]["x"] != self.results[2]["x"]))
