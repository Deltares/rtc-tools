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
from rtctools.optimization.multi_run_mixin import MultiRunMixin
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
    MultiRunMixin,
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

    def run_ids(self) -> int:
        return range(2)

    def seed_files(self):
        """Return a list of seed files."""
        raise NotImplementedError()

    def theta_starts(self):
        """Return a list of theta_start parameters."""
        return [1, 0]

    def seed_from_file(self, file: Path):
        """Create a seed from a gievn file."""
        raise NotImplementedError()

    def seed(self, ensemble_member):
        run_id = self.run_id()
        seed_file = self.seed_files()[run_id]
        if seed_file is None:
            return super().seed(ensemble_member)
        if not self._gp_first_run:
            return super().seed(ensemble_member)
        theta_name = self.homotopy_options()["homotopy_parameter"]
        theta = self.parameters(ensemble_member=0)[theta_name]
        theta_start = self.homotopy_options()["theta_start"]
        if theta > theta_start:
            return super().seed(ensemble_member)
        return self.seed_from_file(seed_file)

    def homotopy_options(self):
        options = super().homotopy_options()
        options["theta_start"] = self.theta_starts()[self.run_id()]
        return options


class ReservoirCSV(
    Reservoir,
    CSVMixin,
    ModelicaMixin,
    CollocatedIntegratedOptimizationProblem,
):
    """Reservoir class using CSV files."""

    def seed_files(self):
        return [DATA_DIR / "seed.csv", None]

    def seed_from_file(self, file: Path):
        times, var_dict = get_timeseries_from_csv(file)
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

    def seed_files(self):
        return [DATA_DIR / "seed.xml", None]

    def seed_from_file(self, file: Path):
        timeseries = PiTimeseries(
            data_config=self.data_config,
            folder=file.parent,
            basename=file.stem,
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
        # Keep track of solver options and seeds.
        self.success = []
        self.seeds_q_out = []

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
        seed = self.seed(ensemble_member=0)
        self.seeds_q_out.append(seed.get("q_out"))
        success = super().optimize(preprocessing, postprocessing, log_solver_failure_as_error)
        if self.enforced_solver_result() is not None:
            success = self.enforced_solver_result()
        self.success.append(success)
        return success


class ReservoirTest(Reservoir, DummySolver):
    """Class for testing a reservoir model."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Keep track of priorities of each run.
        self.priorities = []
        self.thetas = []
        self.used_run_ids = []

    def enforced_solver_result(self):
        # Enforce failure when using a seed.
        return False if self.run_id() == 0 else None

    def priority_started(self, priority: int):
        super().priority_started(priority)
        # Keep track of seeds/priorities/thetas for testing purposes.
        self.used_run_ids.append(self.run_id())
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
        ref_run_ids = [0, 1, 1, 1, 1]
        ref_thetas = [1, 0, 0, 1, 1]
        ref_priorities = [1, 1, 2, 1, 2]
        ref_success = [False, True, True, True, True]
        ref_seeds = [
            Timeseries([0, 1, 2, 3, 4], [1, 1, 2, 3, 3]),
            None,
        ]
        self.assertEqual(model.used_run_ids, ref_run_ids)
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


if __name__ == "__main__":
    test = TestSeedMixin()
    test.test_seeding_with_fallback_csv()
    pass
