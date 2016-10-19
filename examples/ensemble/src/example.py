from rtctools.optimization.collocated_integrated_optimization_problem \
    import CollocatedIntegratedOptimizationProblem
from rtctools.optimization.goal_programming_mixin \
    import GoalProgrammingMixin, Goal
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.control_tree_mixin import ControlTreeMixin
from rtctools.optimization.csv_lookup_table_mixin import CSVLookupTableMixin
from rtctools.util import run_optimization_problem
from rtctools.optimization.timeseries import Timeseries
import numpy as np


class WaterVolumeRangeGoal(Goal):
    def __init__(self, V_min, V_max):
        self.target_min = V_min
        self.target_max = V_max

    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state('storage.V')

    # Enclosure of the function range.
    function_range = (2e5, 6e5)
    function_nominal = 4e5
    priority = 1


class MinimizeQreleaseGoal(Goal):
    # goal programming mixin will try to minimize the following function
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state('Q_release')

    # Every goal needs a rough (over)estimate (enclosure) of the range of the function
    # defined above.
    function_range = (0.0, 6.0)
    # Nominal function value.  Used to scale the goal constraint.
    function_nominal = 2.5
    # The lower the number returned by this function, the higher the priority.
    priority = 2
    # The penalty variable is taken to the order'th power.
    order = 1


class Example(GoalProgrammingMixin, ControlTreeMixin, CSVLookupTableMixin,
              CSVMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    """
    An extention of the goal programming and lookuptable examples that
    demonstrates how to work with ensembles.
    """
    # Overide default csv_ensemble_mode = False from CSVMixin before calling pre()
    csv_ensemble_mode = True

    def pre(self):
        # Do the standard preprocessing
        super(Example, self).pre()

        # Create a dict of empty lists for storing intermediate results from
        # each ensemble
        self.intermediate_results = {
            ensemble_member: [] for ensemble_member in range(self.ensemble_size)}

        # Cache lookup tables for convenience and code legibility
        _lookup_tables = self.lookup_tables(ensemble_member=0)
        self.lookup_storage_V = _lookup_tables['storage_V']

        # Non-varrying goals can be implemented as a timeseries
        for e_m in range(self.ensemble_size):
            self.set_timeseries('H_min', np.ones_like(self.times()) * 0.44,
                                ensemble_member=e_m)
            self.set_timeseries('H_max', np.ones_like(self.times()) * 0.46,
                                ensemble_member=e_m)

            # Q_in is a varying input and is defined in each timeseries_import.csv
            # However, if we set it again here, it will be added to the output files
            self.set_timeseries('Q_in',
                                self.get_timeseries('Q_in', ensemble_member=e_m),
                                ensemble_member=e_m)

            # Convert our water level goals into volume goals
            self.set_timeseries('V_max',
                                self.lookup_storage_V(self.get_timeseries('H_max')),
                                ensemble_member=e_m)
            self.set_timeseries('V_min',
                                self.lookup_storage_V(self.get_timeseries('H_min')),
                                ensemble_member=e_m)

    def path_goals(self):
        g = []
        g.append(WaterVolumeRangeGoal(self.get_timeseries('V_min'),
                                      self.get_timeseries('V_max')))
        g.append(MinimizeQreleaseGoal())
        return g

    def priority_completed(self, priority):
        # We want to print some information about our goal programming problem.
        # We store the useful numbers temporarily, and print information at the
        # end of our run.
        for e_m in range(self.ensemble_size):
            results = self.extract_results(e_m)
            self.set_timeseries('V_storage',  results['storage.V'], ensemble_member=e_m)

            _max = self.get_timeseries('V_max', ensemble_member=e_m).values
            _min = self.get_timeseries('V_min', ensemble_member=e_m).values
            V_storage = self.get_timeseries('V_storage', ensemble_member=e_m).values

            # A little bit of tolerance when checking for acceptance. This
            # tolerance must be set greater than the tolerance of the solver.
            tol = 10
            _max += tol
            _min -= tol
            n_level_satisfied = sum(
                np.logical_and(_min <= V_storage, V_storage <= _max))
            q_release_integral = sum(results['Q_release'])
            self.intermediate_results[e_m].append((priority, n_level_satisfied,
                                                   q_release_integral))

    def post(self):
        super(Example, self).post()
        for e_m in range(self.ensemble_size):
            print('\n\nResults for Ensemble Member {}:'.format(e_m))
            for priority, n_level_satisfied, q_release_integral in \
                    self.intermediate_results[e_m]:
                print("\nAfter finishing goals of priority {}:".format(priority))
                print("Level goal satisfied at {} of {} time steps".format(
                    n_level_satisfied, len(self.times())))
                print("Integral of Q_release = {:.2f}".format(q_release_integral))

    # Any solver options can be set here
    def solver_options(self):
        options = super(Example, self).solver_options()
        options['print_level'] = 1
        return options

# Run
run_optimization_problem(Example, base_folder='..')
