from example_local_control import ExampleLocalControl
from steady_state_initialization_mixin import SteadyStateInitializationMixin
from step_size_parameter_mixin import StepSizeParameterMixin

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.goal_programming_mixin import Goal, GoalProgrammingMixin
from rtctools.optimization.homotopy_mixin import HomotopyMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.util import run_optimization_problem


class TargetLevelGoal(Goal):
    """Really Simple Target Level Goal"""

    def __init__(self, state, target_level):
        self.function_range = target_level - 5.0, target_level + 5.0
        self.function_nominal = target_level
        self.target_min = target_level
        self.target_max = target_level
        self.state = state

    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state(self.state)

    priority = 1


class ExampleOptimization(
    StepSizeParameterMixin,
    SteadyStateInitializationMixin,
    HomotopyMixin,
    GoalProgrammingMixin,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """Goal Programming Approach"""

    def path_goals(self):
        # Add water level goals
        return [
            TargetLevelGoal("dam_upstream.HQUp.H", 20.0),
            TargetLevelGoal("dam_middle.HQUp.H", 15.0),
        ]


# Run
run_optimization_problem(ExampleOptimization)
run_optimization_problem(ExampleLocalControl)
