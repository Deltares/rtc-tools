import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.control_tree_mixin import ControlTreeMixin
from rtctools.optimization.csv_lookup_table_mixin import CSVLookupTableMixin
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.goal_programming_mixin import GoalProgrammingMixin, StateGoal
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.util import run_optimization_problem


class WaterVolumeRangeGoal(StateGoal):
    def __init__(self, optimization_problem):
        # Assign V_min and V_max the the target range
        self.target_min = optimization_problem.get_timeseries("V_min")
        self.target_max = optimization_problem.get_timeseries("V_max")
        super().__init__(optimization_problem)

    state = "storage.V"
    priority = 1


class MinimizeQreleaseGoal(StateGoal):
    # GoalProgrammingMixin will try to minimize the following state
    state = "Q_release"
    # The lower the number returned by this function, the higher the priority.
    priority = 2
    # The penalty variable is taken to the order'th power.
    order = 1


class Example(
    GoalProgrammingMixin,
    CSVMixin,
    CSVLookupTableMixin,
    ModelicaMixin,
    ControlTreeMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """
    An extention of the goal programming and lookuptable examples that
    demonstrates how to work with ensembles.
    """

    # Overide default csv_ensemble_mode = False from CSVMixin before calling pre()
    csv_ensemble_mode = True

    def pre(self):
        # Do the standard preprocessing
        super().pre()

        # Create a dict of empty lists for storing intermediate results from
        # each ensemble
        self.intermediate_results = {
            ensemble_member: [] for ensemble_member in range(self.ensemble_size)
        }

        # Cache lookup tables for convenience and code legibility
        _lookup_tables = self.lookup_tables(ensemble_member=0)
        self.lookup_storage_V = _lookup_tables["storage_V"]

        # Non-varying goals can be implemented as a timeseries
        for e_m in range(self.ensemble_size):
            self.set_timeseries("H_min", np.ones_like(self.times()) * 0.44, ensemble_member=e_m)
            self.set_timeseries("H_max", np.ones_like(self.times()) * 0.46, ensemble_member=e_m)

            # Q_in is a varying input and is defined in each timeseries_import.csv
            # However, if we set it again here, it will be added to the output files
            self.set_timeseries(
                "Q_in", self.get_timeseries("Q_in", ensemble_member=e_m), ensemble_member=e_m
            )

            # Convert our water level goals into volume goals
            self.set_timeseries(
                "V_max", self.lookup_storage_V(self.get_timeseries("H_max")), ensemble_member=e_m
            )
            self.set_timeseries(
                "V_min", self.lookup_storage_V(self.get_timeseries("H_min")), ensemble_member=e_m
            )

    def path_goals(self):
        g = []
        g.append(WaterVolumeRangeGoal(self))
        g.append(MinimizeQreleaseGoal(self))
        return g

    def control_tree_options(self):
        # We want to modify the control tree options, so we override the default
        # control_tree_options method. We call super() to get the default options
        options = super().control_tree_options()
        # Change the branching_times list to only contain the fifth timestep
        options["branching_times"] = [self.times()[5]]
        return options

    def priority_completed(self, priority):
        # We want to print some information about our goal programming problem.
        # We store the useful numbers temporarily, and print information at the
        # end of our run.
        for e_m in range(self.ensemble_size):
            results = self.extract_results(e_m)
            self.set_timeseries("V_storage", results["storage.V"], ensemble_member=e_m)

            _max = self.get_timeseries("V_max", ensemble_member=e_m).values
            _min = self.get_timeseries("V_min", ensemble_member=e_m).values
            V_storage = self.get_timeseries("V_storage", ensemble_member=e_m).values

            # A little bit of tolerance when checking for acceptance. This
            # tolerance must be set greater than the tolerance of the solver.
            tol = 10
            _max += tol
            _min -= tol
            n_level_satisfied = sum(np.logical_and(_min <= V_storage, V_storage <= _max))
            q_release_integral = sum(results["Q_release"])
            self.intermediate_results[e_m].append((priority, n_level_satisfied, q_release_integral))

    def post(self):
        super().post()
        for e_m in range(self.ensemble_size):
            print(f"\n\nResults for Ensemble Member {e_m}:")
            for priority, n_level_satisfied, q_release_integral in self.intermediate_results[e_m]:
                print(f"\nAfter finishing goals of priority {priority}:")
                print(
                    f"Level goal satisfied at {n_level_satisfied} of {len(self.times())} time steps"
                )
                print(f"Integral of Q_release = {q_release_integral:.2f}")

    # Any solver options can be set here
    def solver_options(self):
        options = super().solver_options()
        # When mumps_scaling is not zero, errors occur. RTC-Tools does its own
        # scaling, so mumps scaling is not critical. Proprietary HSL solvers
        # do not exhibit this error.
        solver = options["solver"]
        options[solver]["mumps_scaling"] = 0
        options[solver]["print_level"] = 1
        return options


# Run
run_optimization_problem(Example)
