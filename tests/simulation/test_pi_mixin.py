from test_case import TestCase

from rtctools.simulation.pi_mixin import PIMixin
from rtctools.simulation.simulation_problem import SimulationProblem

from .data_path import data_path


class SimulationModel(PIMixin, SimulationProblem):
    _force_zero_delay = True

    def __init__(self):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="Model",
            model_folder=data_path(),
        )

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class TestSimulation(TestCase):
    def setUp(self):
        self.problem = SimulationModel()

    def test_simulate(self):
        self.problem.simulate()
