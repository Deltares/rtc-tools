from steady_state_initialization_mixin import SteadyStateInitializationMixin
from step_size_parameter_mixin import StepSizeParameterMixin

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.homotopy_mixin import HomotopyMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.util import run_optimization_problem


class ExampleLocalControl(
    StepSizeParameterMixin,
    SteadyStateInitializationMixin,
    HomotopyMixin,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """Local Control Approach"""

    timeseries_export_basename = "timeseries_export_local_control"


if __name__ == "__main__":
    run_optimization_problem(ExampleLocalControl)
