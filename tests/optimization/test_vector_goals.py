import logging

import casadi as ca

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import \
    CollocatedIntegratedOptimizationProblem
from rtctools.optimization.goal_programming_mixin import \
    Goal, GoalProgrammingMixin, StateGoal
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from test_case import TestCase

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

        self._objective_values = []

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
            np.hstack(([self.initial_time, self.times()])),
            np.hstack(([1.0], np.linspace(1.0, 0.0, 21))),
        )
        return constant_inputs

    def bounds(self):
        bounds = super().bounds()
        bounds["u"] = (-2.0, 2.0)
        bounds["x"] = (-5.0, 5.0)
        bounds["z"] = (-5.0, 5.0)
        return bounds

    def goal_programming_options(self):
        options = super().goal_programming_options()
        options['keep_soft_constraints'] = True
        return options

    def set_timeseries(self, timeseries_id, timeseries, ensemble_member, **kwargs):
        # Do nothing
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        return compiler_options

    def priority_completed(self, priority):
        super().priority_completed(priority)
        self._objective_values.append(self.objective_value)


class Goal1(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("x", 0.5, ensemble_member=ensemble_member)

    function_range = (-5.0, 5.0)
    order = 1
    priority = 1
    target_min = 1.0


class Goal2(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("x", 0.7, ensemble_member=ensemble_member)

    function_range = (-5.0, 5.0)
    order = 1
    priority = 1
    target_max = 0.8


class Goal3(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at("x", 1.0, ensemble_member=ensemble_member)

    function_range = (-5.0, 5.0)
    order = 1
    priority = 1
    target_max = 0.5


class Goal4(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.integral("x", 0.1, 1.0, ensemble_member=ensemble_member)

    order = 2
    priority = 2


class ModelGoals(Model):

    def goals(self):
        return [Goal1(), Goal2(), Goal3(), Goal4()]


class Goal1_2_3(Goal):
    def function(self, optimization_problem, ensemble_member):
        return ca.vertcat(
            optimization_problem.state_at("x", 0.5, ensemble_member=ensemble_member),
            optimization_problem.state_at("x", 0.7, ensemble_member=ensemble_member),
            optimization_problem.state_at("x", 1.0, ensemble_member=ensemble_member))

    function_range = (-5.0, 5.0)
    size = 3
    order = 1
    priority = 1
    target_min = np.array([1.0, -np.inf, -np.inf])
    target_max = np.array([np.inf, 0.8, 0.5])


class ModelGoalsVector(ModelGoals):

    def goals(self):
        return [Goal1_2_3(), Goal4()]


class PathGoal1(StateGoal):
    state = "x"
    order = 1
    priority = 1
    target_min = 0.1
    target_max = 1.0


class PathGoal2(StateGoal):
    state = "z"
    order = 1
    priority = 1
    target_min = 0.5
    target_max = 2.0


class PathGoal3(StateGoal):
    state = "x"
    order = 2
    priority = 2


class ModelPathGoals(Model):

    def path_goals(self):
        return [PathGoal1(self), PathGoal2(self), PathGoal3(self)]


class PathGoal1_2(Goal):
    def __init__(self, optimization_problem):
        bounds_x = optimization_problem.bounds()['x']
        bounds_z = optimization_problem.bounds()['z']
        lb = np.array([bounds_x[0], bounds_z[0]])
        ub = np.array([bounds_x[1], bounds_z[1]])
        self.function_range = (lb, ub)

    def function(self, optimization_problem, ensemble_member):
        return ca.vertcat(optimization_problem.state('x'),
                          optimization_problem.state('z'))

    size = 2
    order = 1
    priority = 1
    target_min = np.array([0.1, 0.5])
    target_max = np.array([1.0, 2.0])


class ModelPathGoalsVector(Model):

    def path_goals(self):
        return [PathGoal1_2(self), PathGoal3(self)]


class TestVectorConstraints(TestCase):

    """
    NOTE: As long as the order of goals/constraints is the same, whether or not they are passed
    as a vector or not should not matter. Therefore we often check to see if two problems
    are _exactly_ equal.
    """

    tolerance = 1e-6

    def test_vector_goals(self):
        self.problem1 = ModelGoals()
        self.problem2 = ModelGoalsVector()
        self.problem1.optimize()
        self.problem2.optimize()

        results1 = self.problem1.extract_results()
        results2 = self.problem2.extract_results()

        self.assertAlmostEqual(np.array(self.problem1._objective_values),
                               np.array(self.problem2._objective_values),
                               self.tolerance)
        self.assertAlmostEqual(results1['x'], results2['x'], self.tolerance)

    def test_path_vector_constraints_simple(self):
        self.problem1 = ModelPathGoals()
        self.problem2 = ModelPathGoalsVector()
        self.problem1.optimize()
        self.problem2.optimize()

        results1 = self.problem1.extract_results()
        results2 = self.problem2.extract_results()

        self.assertAlmostEqual(np.array(self.problem1._objective_values),
                               np.array(self.problem2._objective_values),
                               self.tolerance)
        self.assertAlmostEqual(results1['x'], results2['x'], self.tolerance)