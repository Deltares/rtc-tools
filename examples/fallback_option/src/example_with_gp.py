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

    def dummy_solver_should_succeed(self):
        return True

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        # Call the optimize method and pretend it is only succesful
        # when self.dummy_solver_should_succeed() is True.
        super().optimize(preprocessing, postprocessing, log_solver_failure_as_error)
        success = self.dummy_solver_should_succeed()
        return success


class MultiRunMixin(OptimizationProblem):
    """
    Enables a workflow to solve an optimization problem with multiple attempts.
    """

    def __init__(self, **kwargs):
        self.solver = "ipopt"  # Solver, by default ipopt.
        super().__init__(**kwargs)

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
    """
    An example of automatically switching to a different solver during goal programming.

    This class inherits from the DummySolver class to enforce a solver result,
    which is only used to illustrate how the fallback can be implemented.

    The MultiRunMixin class should be inherited after GoalProgrammingMixin.
    This way, the solver loop is applied for each priority during goal programming.
    """

    def __init__(self, **kwargs):
        # Keep track of the current priority.
        # This is only used in this example to determine the result of the dummy solver.
        self.priority = None
        super().__init__(**kwargs)

    def goals(self):
        return [DummyGoal(priority=prio) for prio in range(3)]

    def solver_options(self):
        options = super().solver_options()
        if self.solver == "ipopt":
            options["solver"] = "ipopt"
        elif self.solver == "highs":
            options["casadi_solver"] = "qpsol"
            options["solver"] = "highs"
        else:
            raise ValueError(f"Solver should be 'ipopt' or 'highs', not {self.solver}.")
        return options

    def priority_started(self, priority):
        # Keep track of the current priority.
        # This is only used in this example to determine the result of the dummy solver.
        self.priority = priority
        super().priority_started(priority)

    def dummy_solver_should_succeed(self):
        # Provide some logic for when the dummy solver should fail.
        # This is just to illustrate the fallback option.
        if self.priority == 1 and self.solver == "ipopt":
            return False
        return True


# Try solving the optimization problem.
problem = run_optimization_problem(Example, base_folder=BASIC_EXAMPLE_FOLDER)
