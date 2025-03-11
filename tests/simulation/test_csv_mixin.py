import logging
import math
import os

import rtctools.data.csv as csv
from rtctools.simulation.csv_mixin import CSVMixin

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)

TOL = 1e-6  # tolerance for tests


class Model(CSVMixin):
    _force_zero_delay = True

    def __init__(self, **kwargs):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="Model",
            model_folder=data_path(),
        )
        self.output = None

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options

    def read(self):
        super().read()

        # set some additional parameters
        self.io.set_parameter("x_start", 1.02)

    def read_output(self):
        """Read the output stored in timeseries_export.csv"""
        self.output = csv.load(
            os.path.join(data_path(), "timeseries_export.csv"),
            delimiter=",",
            with_time=True,
        )

    def get_reference_solution_first_timestep(self):
        """Get a reference solution for the first time step"""
        time_index = 1
        time = self.times()[time_index]
        dt = self.get_time_step()
        x_start = 1.02
        k = 1.01
        u = 2.0
        # Time step uses the implicit Euler scheme.
        x = (x_start + dt * u) / (1 - dt * k)
        y = 3 - x
        z = x**2 + math.sin(time)
        return {"y": y, "z": z}


class TestCSVMixin(TestCase):
    def setUp(self):
        self.problem = Model()
        self.problem.read()
        self.tolerance = 1e-6

    def test_parameter(self):
        """Test setting and reading the parameters.

        Parameters are read from the file parameters.csv
        or set manually in the CSVMixin.read function.
        """
        params = self.problem.parameters()
        self.assertAlmostEqual(params["k"], 1.01, self.tolerance)
        self.assertAlmostEqual(params["x_start"], 1.02, self.tolerance)

    def test_initial_state(self):
        """Test setting and reading the initial state.

        Only the initial state of variables in the files initial_state.csv
        and timeseries_import.csv are read.
        """
        self.problem.initialize()
        initial_state = self.problem.initial_state()
        self.assertAlmostEqual(initial_state["x"], 1.02, self.tolerance)
        self.assertAlmostEqual(initial_state["u"], 8.8, self.tolerance)
        self.assertAlmostEqual(initial_state["constant_input"], 1.0, self.tolerance)

    def test_write(self):
        """Test writing output to the file timeseries_export.xml."""
        self.problem.initialize()
        self.problem.update(-1)
        self.problem.write()
        self.problem.read_output()
        time_index = 1
        output = self.problem.output[time_index]
        ref = self.problem.get_reference_solution_first_timestep()
        self.assertAlmostEqual(output["y"], ref["y"], tol=TOL)
        self.assertAlmostEqual(output["z"], ref["z"], tol=TOL)
