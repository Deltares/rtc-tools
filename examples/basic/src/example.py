from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.util import run_optimization_problem


class Example(CSVMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    """
    A basic example for introducing users to RTC-Tools 2
    """

    def objective(self, ensemble_member):
        # Minimize water pumped. The total water pumped is the integral of the
        # water pumped from the starting time until the stopping time. In
        # practice, self.integral() is a summation of all the discrete states.
        return self.integral("Q_release", ensemble_member=ensemble_member)

    def path_constraints(self, ensemble_member):
        # Call super() class to not overwrite default behaviour
        constraints = super().path_constraints(ensemble_member)
        # Constrain the volume of storage between 380000 and 420000 m^3
        constraints.append((self.state("storage.V"), 380000, 420000))
        return constraints

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["basemodelica"] = True
        compiler_options["cache"] = False
        return compiler_options

# Run
run_optimization_problem(Example)
