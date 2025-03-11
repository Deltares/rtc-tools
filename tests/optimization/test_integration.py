import logging

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.goal_programming_mixin import Goal, GoalProgrammingMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")


class SingleShootingBaseModel(ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="SingleShootingModel",
            model_folder=data_path(),
        )

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    @property
    def integrate_states(self):
        return True

    def pre(self):
        # Do nothing
        pass

    def constant_inputs(self, ensemble_member):
        return {"constant_input": Timeseries(self.times(), np.linspace(1.0, 0.0, 21))}

    def bounds(self):
        # Variable bounds
        return {"u": (-2.0, 2.0)}

    def seed(self, ensemble_member):
        # No particular seeding
        return {}

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


class SingleShootingModel(SingleShootingBaseModel):
    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2


class TestSingleShooting(TestCase):
    def test_objective_value(self):
        self.assertAlmostLessThan(abs(self.problem.objective_value), 0.0, self.tolerance)

    def test_state(self):
        times = self.problem.times()
        parameters = self.problem.parameters(0)
        self.assertAlmostEqual(
            (self.results["x"][1:] - self.results["x"][:-1]) / (times[1:] - times[:-1]),
            parameters["k"] * self.results["x"][1:] + self.results["u"][1:],
            self.tolerance,
        )
        self.assertAlmostEqual(
            (self.results["w"][1:] - self.results["w"][:-1]) / (times[1:] - times[:-1]),
            self.results["x"][1:],
            self.tolerance,
        )

    def test_algebraic_variable(self):
        constant_input = self.problem.constant_inputs(0)["constant_input"]
        self.assertAlmostEqual(
            self.results["a"],
            self.results["x"] + self.results["w"] + constant_input.values,
            self.tolerance,
        )

    def setUp(self):
        self.problem = SingleShootingModel()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6


class SingleShootingGoalProgrammingModel(GoalProgrammingMixin, SingleShootingBaseModel):
    def goals(self):
        return [Goal1(), Goal2(), Goal3()]

    def path_goals(self):
        return [PathGoal1()]

    def set_timeseries(self, timeseries_id, timeseries, ensemble_member, **kwargs):
        # Do nothing
        pass


class PathGoal1(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state("x")

    function_range = (-1e1, 1e1)
    priority = 1
    target_min = -0.9e1
    target_max = 0.9e1


class Goal1(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("x", 0.5, ensemble_member=ensemble_member)

    function_range = (-1e1, 1e1)
    priority = 3
    target_min = 0.0


class Goal2(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("x", 0.7, ensemble_member=ensemble_member)

    function_range = (-1e1, 1e1)
    priority = 3
    target_min = 0.1


class Goal3(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.integral("x", 0.1, 1.0, ensemble_member=ensemble_member)

    function_range = (-1e1, 1e1)
    priority = 2
    target_max = 1.0


class TestGoalProgramming(TestCase):
    def setUp(self):
        self.problem = SingleShootingGoalProgrammingModel()
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_x(self):
        self.assertAlmostGreaterThan(
            self.problem.interpolate(
                0.7, self.problem.times(), self.problem.extract_results()["x"]
            ),
            0.1,
            self.tolerance,
        )


class SingleShootingEnsembleModel(SingleShootingBaseModel):
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


class TestEnsemble(TestCase):
    def setUp(self):
        self.problem = SingleShootingEnsembleModel()
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_states(self):
        times = self.problem.times()
        for ensemble_member in range(self.problem.ensemble_size):
            parameters = self.problem.parameters(ensemble_member)
            results = self.problem.extract_results(ensemble_member)
            self.assertAlmostEqual(
                (results["x"][1:] - results["x"][:-1]) / (times[1:] - times[:-1]),
                parameters["k"] * results["x"][1:] + results["u"][1:],
                self.tolerance,
            )
            self.assertAlmostEqual(
                (results["w"][1:] - results["w"][:-1]) / (times[1:] - times[:-1]),
                results["x"][1:],
                self.tolerance,
            )

    def test_algebraic_variables(self):
        for ensemble_member in range(self.problem.ensemble_size):
            results = self.problem.extract_results(ensemble_member)
            constant_input = self.problem.constant_inputs(ensemble_member)["constant_input"]
            self.assertAlmostEqual(
                results["a"], results["x"] + results["w"] + constant_input.values, self.tolerance
            )


class OldApiErrorModel(SingleShootingBaseModel):
    """
    Test that an exception is raised when the old API is used, and that
    it points users to the new API.
    """

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2

    @property
    def integrated_states(self):
        return [*self.algebraic_states, *self.differentiated_states]

    @property
    def integrate_states(self):
        return False


class OldApiErrorTest(TestCase):
    def test_integration_exception_raised(self):
        with self.assertRaisesRegex(
            Exception,
            "The integrated_states property is no longer supported. Use integrate_states instead",
        ):
            self.problem.optimize()

    def setUp(self):
        self.problem = OldApiErrorModel()
