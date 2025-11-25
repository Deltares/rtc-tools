import bisect
import os

import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.pi_mixin import PIMixin

from ..test_case import TestCase
from .data_path import data_path


class Model(PIMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    pi_parameter_config_basenames = ["rtcParameterConfig", "rtcParameterConfig_extra"]
    pi_check_for_duplicate_parameters = True

    pi_binary_timeseries = False
    pi_validate_timeseries = False

    def __init__(self, model_data_path=None):
        if model_data_path is None:
            model_data_path = data_path()
        super().__init__(
            input_folder=model_data_path,
            output_folder=model_data_path,
            model_name="Model",
            model_folder=model_data_path,
        )

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        f = xf**2
        return f

    def constraints(self, ensemble_member):
        # No additional constraints
        return []

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class TestPIMixin(TestCase):
    def setUp(self):
        self.problem = Model()
        self.problem.optimize()
        self.results = self.problem.extract_results()
        self.tolerance = 1e-6

    def test_parameter(self):
        params = self.problem.parameters(0)
        self.assertEqual(params["k"], 1.01)
        self.assertEqual(params["j"], 12.01)
        self.assertEqual(params["y"], 12.02)
        self.assertEqual(params["SV_H_y"], 22.02)
        self.assertEqual(params["SV_H_y"], params["SV_V_y"])

    def test_history(self):
        history = self.problem.history(0)
        self.assertAlmostEqual(history["x"].values[-1], 1.02, self.tolerance)
        self.assertAlmostEqual(history["v_initial"].values[-1], 2.1, self.tolerance)

    def test_seed(self):
        seed = self.problem.seed(0)
        self.assertAlmostEqual(seed["x"].values[2], 0.03, self.tolerance)

    def test_objective_value(self):
        objective_value_tol = 1e-6
        self.assertTrue(abs(self.problem.objective_value) < objective_value_tol)

    def test_output(self):
        self.assertAlmostEqual(
            self.results["x"] ** 2 + np.sin(self.problem.times()),
            self.results["z"],
            self.tolerance,
        )

    def test_algebraic(self):
        self.assertAlmostEqual(
            self.results["y"] + self.results["x"],
            np.ones(len(self.problem.times())) * 3.0,
            self.tolerance,
        )

    def test_bounds(self):
        self.assertAlmostGreaterThan(self.results["u"], -2, self.tolerance)
        self.assertAlmostLessThan(self.results["u"], 2, self.tolerance)

    def test_interpolation(self):
        t_idx = bisect.bisect_left(self.problem.io.times_sec, 0.0)

        t = (
            self.problem.get_timeseries("x", 0).times[t_idx + 1]
            + (
                self.problem.get_timeseries("x", 0).times[t_idx + 2]
                - self.problem.get_timeseries("x", 0).times[t_idx + 1]
            )
            / 2
        )
        x_ref = (
            self.problem.get_timeseries("x", 0).values[t_idx + 1]
            + self.problem.get_timeseries("x", 0).values[t_idx + 2]
        ) / 2
        self.assertAlmostEqual(self.problem.timeseries_at("x", t), x_ref, self.tolerance)

    def test_ensemble_member_indexes(self):
        # we expect a value error when ensembele member indexes are not zero-based and
        # increasing by one
        with self.assertRaises(ValueError):
            print(os.path.join(data_path(), "non_zero_indexed_ensembles"))
            self.problem0 = Model(
                model_data_path=os.path.join(data_path(), "non_zero_indexed_ensembles"),
            )
            self.problem0.optimize()
        # We expect no error when there is only one ensemble member (with a non-zero
        # index)
        self.problem1 = Model(
            model_data_path=os.path.join(data_path(), "single_non_zero_ensemble_index"),
        )
        self.problem1.optimize()
