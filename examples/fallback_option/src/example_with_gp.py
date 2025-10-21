import logging
from pathlib import Path

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.goal_programming_mixin import Goal, GoalProgrammingMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.util import run_optimization_problem

logger = logging.getLogger("rtctools")

BASIC_EXAMPLE_FOLDER = Path(__file__).parents[2] / "basic"


class DummySolver(OptimizationProblem):
    """
    Class for enforcing a solver result.

    This class enforces a solver result
    and is just used for illustrating how to implement a fallback option.
    """

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        # Call the optimize method and pretend it is only successful when using the 'highs' solver.
        super().optimize(preprocessing, postprocessing, log_solver_failure_as_error)
        solver = self.solver_options()["solver"]
        success = solver == "highs"
        return success


class MultiRunMixin(OptimizationProblem):
    """
    Enables a workflow to solve an optimization problem with multiple attempts.
    """

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        # Overwrite the optimize method to try different solvers if the previous solver fails.
        if preprocessing:
            self.pre()
        solvers = ["ipopt", "highs"]
        for solver in solvers:
            self.solver = solver
            success = super().optimize(
                preprocessing=False,
                postprocessing=False,
                log_solver_failure_as_error=log_solver_failure_as_error,
            )
            logger.info(f"Finished running solver {solver} with success = {success}.")
            if success:
                break
        if postprocessing:
            self.post()
        return success


class DummyGoal(Goal):
    """ "Goal to illustrate the fallback option during goal programming."""

    def __init__(self, priority):
        super().__init__()
        self.priority = priority

    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.integral("Q_release")


class Example(
    GoalProgrammingMixin,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
    MultiRunMixin,
    DummySolver,
):
    # initially the solver is set to None
    solver = None
    """
    An example of automatically switching to a different solver during goal programming.

    This class inherits from the DummySolver class to enforce a solver result,
    which is only used to illustrate how the fallback can be implemented.

    The MultiRunMixin class should be inherited after GoalProgrammingMixin.
    This way, the solver loop is applied for each priority during goal programming.
    """

    def goals(self):
        return [DummyGoal(priority=prio) for prio in range(3)]

    def solver_options(self):
        options = super().solver_options()
        if self.solver == "ipopt":
            options["solver"] = "ipopt"
        elif self.solver == "highs":
            options["casadi_solver"] = "qpsol"
            options["solver"] = "highs"
            options["highs"] = {"time_limit": 1}
        elif self.solver:
            raise ValueError(f"Solver should be 'ipopt' or 'highs', not {self.solver}.")
        return options


# Try solving the optimization problem.
problem = run_optimization_problem(Example, base_folder=BASIC_EXAMPLE_FOLDER)
