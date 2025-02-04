import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_lookup_table_mixin import CSVLookupTableMixin
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.goal_programming_mixin import GoalProgrammingMixin, StateGoal
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.util import run_optimization_problem


class WaterVolumeRangeGoal(StateGoal):
    # We want to add a water volume range goal to our optimization. However, at
    # the time of defining this goal we still do not know what the value of the
    # min and max are. We add an __init__() method so that the values of these
    # goals can be defined when the optimization problem class instantiates
    # this goal.
    def __init__(self, optimization_problem):
        # Assign V_min and V_max the the target range
        self.target_min = optimization_problem.get_timeseries("V_min")
        self.target_max = optimization_problem.get_timeseries("V_max")
        super().__init__(optimization_problem)

    state = "storage.V"
    priority = 1


class MinimizeQreleaseGoal(StateGoal):
    # GoalProgrammingMixin will try to minimize the following state:
    state = "Q_release"
    # The lower the number returned by this function, the higher the priority.
    priority = 2
    # The penalty variable is taken to the order'th power.
    order = 1


class Example(
    GoalProgrammingMixin,
    CSVLookupTableMixin,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """
    An extention of the goal programming example that shows how to incorporate
    non-linear storage elements in the model.
    """

    def pre(self):
        super().pre()
        # Empty list for storing intermediate_results
        self.intermediate_results = []

        # Cache lookup tables for convenience and legibility
        _lookup_tables = self.lookup_tables(ensemble_member=0)
        self.lookup_storage_V = _lookup_tables["storage_V"]

        # Non-varrying goals can be implemented as a timeseries like this:
        self.set_timeseries("H_min", np.ones_like(self.times()) * 0.44, output=False)

        # Q_in is a varying input and is defined in timeseries_import.csv
        # However, if we set it again here, it will be added to the output file
        self.set_timeseries("Q_in", self.get_timeseries("Q_in"))

        # Convert our water level constraints into volume constraints
        self.set_timeseries("V_max", self.lookup_storage_V(self.get_timeseries("H_max")))
        self.set_timeseries("V_min", self.lookup_storage_V(self.get_timeseries("H_min")))

    def path_goals(self):
        g = []
        g.append(WaterVolumeRangeGoal(self))
        g.append(MinimizeQreleaseGoal(self))
        return g

    # We want to print some information about our goal programming problem. We
    # store the useful numbers temporarily, and print information at the end of
    # our run (see post() method below).
    def priority_completed(self, priority):
        results = self.extract_results()
        self.set_timeseries("storage_V", results["storage.V"])

        _max = self.get_timeseries("V_max").values
        _min = self.get_timeseries("V_min").values
        storage_V = self.get_timeseries("storage_V").values

        # A little bit of tolerance when checking for acceptance.
        tol = 10
        _max += tol
        _min -= tol
        n_level_satisfied = sum(np.logical_and(_min <= storage_V, storage_V <= _max))
        q_release_integral = sum(results["Q_release"])
        self.intermediate_results.append((priority, n_level_satisfied, q_release_integral))

    def post(self):
        # Call super() class to not overwrite default behaviour
        super().post()
        for priority, n_level_satisfied, q_release_integral in self.intermediate_results:
            print("\nAfter finishing goals of priority {}:".format(priority))
            print(
                "Volume goal satisfied at {} of {} time steps".format(
                    n_level_satisfied, len(self.times())
                )
            )
            print("Integral of Q_release = {:.2f}".format(q_release_integral))

    # Any solver options can be set here
    def solver_options(self):
        options = super().solver_options()
        solver = options["solver"]
        options[solver]["print_level"] = 1
        return options


# Run
run_optimization_problem(Example)
