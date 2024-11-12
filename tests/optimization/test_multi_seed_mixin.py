from pathlib import Path

from rtctools.data.pi import Timeseries as PiTimeseries
from rtctools.data.util import (
    fill_nan_in_timeseries,
)
from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin, get_timeseries_from_csv
from rtctools.optimization.goal_programming_mixin import Goal, GoalProgrammingMixin, StateGoal
from rtctools.optimization.homotopy_mixin import HomotopyMixin
from rtctools.optimization.io_mixin import IOMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.multi_seed_mixin import MultiSeedMixin
from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.optimization.pi_mixin import PIMixin
from rtctools.optimization.timeseries import Timeseries
from test_case import TestCase

DATA_DIR = Path(__file__).parent / "data" / "reservoir"


class WaterVolumeGoal(StateGoal):
    """Keep the volume within a given range."""

    priority = 1
    state = "volume"
    target_min = 10
    target_max = 15


class MinimizeQOutGoal(Goal):
    """Minimize the outflow."""

    priority = 2

    def function(self, optimization_problem, ensemble_member):
        del self
        del ensemble_member
        return optimization_problem.integral("q_out")


class Reservoir(
    MultiSeedMixin,
    HomotopyMixin,
    GoalProgrammingMixin,
    IOMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
    OptimizationProblem,
):
    """Optimization problem for controlling a reservoir."""

    def __init__(self, **kwargs):
        kwargs["model_name"] = "Reservoir"
        kwargs["input_folder"] = DATA_DIR
        kwargs["output_folder"] = DATA_DIR
        kwargs["model_folder"] = DATA_DIR
        super().__init__(**kwargs)

    def bounds(self):
        bounds = super().bounds()
        bounds["volume"] = (0, 20.0)
        return bounds

    def goals(self):
        del self
        return [MinimizeQOutGoal()]

    def path_goals(self):
        return [WaterVolumeGoal(self)]

    def seed_ids(self):
        return [DATA_DIR / "seed.csv", None]

    def use_seed_id(self):
        if not self._gp_first_run:
            return False
        theta_name = self.homotopy_options()["homotopy_parameter"]
        theta = self.parameters(ensemble_member=0)[theta_name]
        theta_start = self.homotopy_options()["theta_start"]
        if theta > theta_start:
            return False
        return True

    def homotopy_options(self):
        options = super().homotopy_options()
        if self.selected_seed_id() is not None:
            options["theta_start"] = 1.0
        return options


class ReservoirCSV(
    Reservoir,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """Reservoir class using CSV files."""

    def seed_from_id(self, seed_id: Path):
        times, var_dict = get_timeseries_from_csv(seed_id)
        times_sec = self.io.datetime_to_sec(times, self.io.reference_datetime)
        seed = {}
        for var, values in var_dict.items():
            values = fill_nan_in_timeseries(times, values)
            seed[var] = Timeseries(times_sec, values)
        return seed


class ReservoirPI(
    Reservoir,
    PIMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """Reservoir class using Delft-FEWS Published Interface files."""

    pi_parameter_config_basenames = []

    def seed_from_id(self, seed_id: Path):
        timeseries = PiTimeseries(
            data_config=self.data_config,
            folder=seed_id.parent,
            basename=seed_id.stem,
            binary=False,
        )
        times = timeseries.times
        times_sec = self.io.datetime_to_sec(times, self.io.reference_datetime)
        seed = {}
        for var, values in timeseries.items():
            values = fill_nan_in_timeseries(times, values)
            seed[var] = Timeseries(times_sec, values)
        return seed


class DummySolver(OptimizationProblem):
    """Class for enforcing a solver result for testing purposes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.success = []  # Keep track of solver results.

    def enforced_solver_result(self):
        """Return the enforced solver result."""
        del self
        return None

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        success = super().optimize(preprocessing, postprocessing, log_solver_failure_as_error)
        if self.enforced_solver_result() is not None:
            success = self.enforced_solver_result()
        self.success.append(success)
        return success


class ReservoirTest(Reservoir, DummySolver):
    """Class for testing a reservoir model."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Keep track of seeds/priorities/thetas of each run.
        self.seeds_q_out = []
        self.priorities = []
        self.thetas = []
        self.used_seeds = []

    def enforced_solver_result(self):
        # Enforce failure when using a seed.
        return False if self.selected_seed_id() is not None else None

    def priority_started(self, priority: int):
        super().priority_started(priority)
        # Keep track of seeds/priorities/thetas for testing purposes.
        seed = self.seed(ensemble_member=0)
        self.seeds_q_out.append(seed.get("q_out"))
        self.used_seeds.append(self.selected_seed_id() is not None)
        self.priorities.append(priority)
        self.thetas.append(self.parameters(ensemble_member=0)["theta"])


class ReservoirCSVTest(ReservoirTest, ReservoirCSV, DummySolver):
    """ReservoirTest class using CSV files."""

    pass


class ReservoirPITest(ReservoirTest, ReservoirPI, DummySolver):
    """ReservoirTest class using Delft-FEWS Published Interface files."""

    pass


class TestSeedMixin(TestCase):
    """Test class for seeding with fallback."""

    def _test_seeding_with_fallback(self, model: ReservoirTest):
        """Test using a seed from a file with a fallback option."""
        model.optimize()
        ref_used_seeds = [True, False, False, False, False]
        ref_thetas = [1, 0, 0, 1, 1]
        ref_priorities = [1, 1, 2, 1, 2]
        ref_success = [False, True, True, True, True]
        ref_seeds = [
            Timeseries([0, 1, 2, 3, 4], [1, 1, 2, 3, 3]),
            None,
        ]
        self.assertEqual(model.used_seeds, ref_used_seeds)
        self.assertEqual(model.thetas, ref_thetas)
        self.assertEqual(model.priorities, ref_priorities)
        self.assertEqual(model.success, ref_success)
        self.assertEqual(model.seeds_q_out[:2], ref_seeds)

    def test_seeding_with_fallback_csv(self):
        """Test using a seed from a CSV file with a fallback option."""
        model = ReservoirCSVTest()
        self._test_seeding_with_fallback(model)

    def test_seeding_with_fallback_pi(self):
        """Test using a seed from a PI file with a fallback option."""
        model = ReservoirPITest()
        self._test_seeding_with_fallback(model)
