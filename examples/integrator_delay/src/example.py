"""
Examples for optimization/simulation problems with a delay component.

The examples use the same model and result in the same output.
"""

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin as CSVMixinOpt
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.simulation.csv_mixin import CSVMixin as CSVMixinSim
from rtctools.simulation.simulation_problem import SimulationProblem
from rtctools.util import run_optimization_problem, run_simulation_problem


class ExampleOpt(CSVMixinOpt, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    """
    An optimization problem example containing a delay component
    """

    def __init__(self, **kwargs):
        super().__init__(model_name="Example", **kwargs)

    def path_objective(self, ensemble_member):
        # The goal is that the volume stays as close to v_ideal as possible.
        del ensemble_member
        v_ideal = 400000
        return (self.state("integrator.V") - v_ideal) ** 2


class ExampleSim(CSVMixinSim, SimulationProblem):
    """
    A simulation problem example containing a delay component
    """

    timeseries_import_basename = "timeseries_import_simulation"
    timeseries_export_basename = "timeseries_export_simulation"

    def __init__(self, **kwargs):
        dt_hours = 12
        dt = dt_hours * 3600
        super().__init__(model_name="Example", fixed_dt=dt, **kwargs)


# Solve optimization problem
run_optimization_problem(ExampleOpt)
# Rum simulation
run_simulation_problem(ExampleSim)
