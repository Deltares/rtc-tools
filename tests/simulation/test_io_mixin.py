from datetime import datetime, timedelta

import numpy as np
from test_case import TestCase

from rtctools.simulation.io_mixin import IOMixin
from rtctools.simulation.simulation_problem import SimulationProblem

from .data_path import data_path


class DummyIOMixin(IOMixin):
    def read(self):
        # fill with dummy data
        ref_datetime = datetime(2000, 1, 1)
        self.io.reference_datetime = ref_datetime
        times_sec = [-7200, -3600, 0, 3600, 7200, 9800]
        datetimes = [ref_datetime + timedelta(seconds=x) for x in times_sec]

        values = {
            "constant_input": [1.1, 1.4, 0.9, 1.2, 1.5, 1.7],
            "u": [0.5, 0.2, 0.3, 0.1, 0.4, 0.0],
        }

        for key, value in values.items():
            self.io.set_timeseries(key, datetimes, np.array(value))

        # set some parameters as well
        self.io.set_parameter("k", 1.01)
        self.io.set_parameter("x_start", 1.02)

    def write(self):
        pass


class Model(DummyIOMixin, SimulationProblem):
    _force_zero_delay = True

    def __init__(self, **kwargs):
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


class TestDummyIOMixin(TestCase):
    def setUp(self):
        self.problem = Model()
        self.problem.read()

    def test_initialize(self):
        self.assertTrue(np.isnan(self.problem.get_var("u")))
        self.assertTrue(np.isnan(self.problem.get_var("constant_input")))
        self.assertTrue(np.isnan(self.problem.get_var("k")))
        self.assertTrue(np.isnan(self.problem.get_var("x_start")))

        self.problem.initialize()

        self.assertEqual(self.problem.get_var("u"), 0.3)
        self.assertEqual(self.problem.get_var("constant_input"), 0.9)
        self.assertEqual(self.problem.get_var("k"), 1.01)
        self.assertEqual(self.problem.get_var("x_start"), 1.02)

        self.assertEqual(self.problem.get_var("x"), 1.02)  # x should start equal to x_start
        self.assertEqual(self.problem.get_var("alias"), 1.02)  # x = alias
        self.assertEqual(self.problem.get_var("w"), 0.0)  # w should start at 0.0
        self.assertEqual(self.problem.get_var("y"), 1.98)  # x + y = 3.0
        self.assertEqual(self.problem.get_var("z"), 1.0404)  # z = x^2 + sin(time)
        self.assertEqual(self.problem.get_var("u_out"), 1.3)  # u_out = u + 1
        self.assertEqual(self.problem.get_var("switched"), 1.0)  # 1.0 if x > 0.5 else 2.0
        self.assertEqual(
            self.problem.get_var("constant_output"), 0.9
        )  # constant_output = constant_input
        # todo add check for x_delayed once delay is properly implemented

        for output_variable in self.problem._io_output_variables:
            self.assertEqual(
                self.problem._io_output[output_variable][0], self.problem.get_var(output_variable)
            )

    def test_update(self):
        self.problem.initialize()
        self.problem.update(-1)

        self.assertEqual(self.problem.get_var("u"), 0.1)
        self.assertEqual(self.problem.get_var("constant_input"), 1.2)
        self.assertEqual(self.problem.get_var("k"), 1.01)
        self.assertEqual(self.problem.get_var("x_start"), 1.02)

        self.assertEqual(self.problem.get_var("u_out"), 1.1)  # u_out = u + 1
        self.assertEqual(self.problem.get_var("switched"), 2.0)  # 1.0 if x > 0.5 else 2.0
        self.assertEqual(
            self.problem.get_var("constant_output"), 1.2
        )  # constant_output = constant_input

        for output_variable in self.problem._io_output_variables:
            self.assertEqual(
                self.problem._io_output[output_variable][-1], self.problem.get_var(output_variable)
            )

    def test_times(self):
        self.assertTrue(np.array_equal(self.problem.times(), [0, 3600, 7200, 9800]))

    def test_parameters(self):
        parameters = self.problem.parameters()

        self.assertEqual(len(parameters), 2)
        self.assertEqual(parameters["k"], 1.01)
        self.assertEqual(parameters["x_start"], 1.02)

    def test_timeseries_at(self):
        self.assertEqual(self.problem.timeseries_at("u", 3600), 0.1)  # no interpolation needed
        self.assertEqual(self.problem.timeseries_at("u", 1800), (0.3 + 0.1) / 2)  # interpolation
