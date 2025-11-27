import logging

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.goal_programming_mixin import (
    Goal,
    GoalProgrammingMixin,
    StateGoal,
)
from rtctools.optimization.min_abs_goal_programming_mixin import (
    MinAbsGoal,
    MinAbsGoalProgrammingMixin,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)


class Model(GoalProgrammingMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="ModelWithInitial",
            model_folder=data_path(),
        )

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    def parameters(self, ensemble_member):
        parameters = super().parameters(ensemble_member)
        parameters["u_max"] = 2.0
        return parameters

    def constant_inputs(self, ensemble_member):
        constant_inputs = super().constant_inputs(ensemble_member)
        constant_inputs["constant_input"] = Timeseries(
            np.hstack([self.initial_time, self.times()]),
            np.hstack(([1.0], np.linspace(1.0, 0.0, 21))),
        )
        return constant_inputs

    def bounds(self):
        bounds = super().bounds()
        bounds["u"] = (-2.0, 2.0)
        return bounds

    def set_timeseries(self, timeseries_id, timeseries, ensemble_member, **kwargs):
        # Do nothing
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class GoalMinimizeU(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("u", 0.5, ensemble_member=ensemble_member)

    priority = 1
    order = 1


class GoalPrio2MinimizeU(GoalMinimizeU):
    priority = 2


class GoalMinimizeSqU(GoalPrio2MinimizeU):
    order = 2


class GoalMinimizeAbsU(MinAbsGoal, GoalPrio2MinimizeU):
    pass


class InvalidGoalTargetAbsU(GoalMinimizeAbsU):
    target_min = 0.0
    function_range = (0.0, 10.0)


class GoalTargetU(StateGoal):
    state = "u"
    target_min = -1.9
    target_max = 1.9
    priority = 1


class ModelTargetU(Model):
    def path_goals(self):
        return [GoalTargetU(self)]


class ModelTargetMinimizeU(ModelTargetU):
    def goals(self):
        return [GoalPrio2MinimizeU()]

    def path_goals(self):
        return [GoalTargetU(self)]


class ModelInvalidAbsoluteGoal(ModelTargetU, MinAbsGoalProgrammingMixin, GoalProgrammingMixin):
    def min_abs_goals(self):
        return [InvalidGoalTargetAbsU()]


class ModelMinimizeSqU(ModelTargetU):
    def goals(self):
        return [GoalMinimizeSqU()]


class ModelMinimizeAbsU(ModelTargetU, MinAbsGoalProgrammingMixin, GoalProgrammingMixin):
    def min_abs_goals(self):
        return [GoalMinimizeAbsU()]


class TestAbsoluteMinimization(TestCase):
    def setUp(self):
        self.tolerance = 1e-5

    def test_exception_absolute_target(self):
        self.problem = ModelInvalidAbsoluteGoal()

        with self.assertRaisesRegex(Exception, "only allowed for minimization"):
            self.problem.optimize()

    def test_negative_variable_different(self):
        self.problem1 = ModelTargetMinimizeU()
        self.problem2 = ModelMinimizeAbsU()

        self.problem1.optimize()
        self.problem2.optimize()

        self.assertAlmostEqual(self.problem1.objective_value, -1.9, self.tolerance)
        self.assertGreaterEqual(self.problem2.objective_value, 0.0 - self.tolerance)

    def test_squared_versus_absolute(self):
        self.problem1 = ModelMinimizeSqU()
        self.problem2 = ModelMinimizeAbsU()

        self.problem1.optimize()
        self.problem2.optimize()

        self.assertAlmostEqual(
            self.problem1.objective_value, self.problem2.objective_value**2, self.tolerance
        )
