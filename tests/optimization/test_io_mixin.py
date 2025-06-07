import bisect
import logging
from datetime import datetime, timedelta
from unittest import TestCase

import casadi as ca
import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.io_mixin import IOMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)


class DummyIOMixin(IOMixin):
    def read(self):
        # fill with dummy data
        ref_datetime = datetime(2000, 1, 1)
        self.io.reference_datetime = ref_datetime
        times_sec = [-7200, -3600, 0, 3600, 7200, 9800]
        datetimes = [ref_datetime + timedelta(seconds=x) for x in times_sec]

        values = {
            "constant_input": [1.1, 1.4, 0.9, 1.2, 1.5, 1.7],
            "u_Min": [0.5, 0.2, 0.3, 0.1, 0.4, 0.0],
            "u_Max": [2.1, 2.2, 2.0, 2.4, 2.5, 2.3],
            "alias": [3.1, 3.2, 3.3, 3.4, 3.5, 3.6],  # alias of 'x'
        }

        for key, value in values.items():
            self.io.set_timeseries(key, datetimes, np.array(value))

    def write(self):
        pass

    def times(self, variable=None):
        if hasattr(self, "_overrule_times"):
            return self._overrule_times
        else:
            return super().times(variable)


class Model(DummyIOMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self, **kwargs):
        kwargs["model_name"] = kwargs.get("model_name", "Model")
        kwargs["input_folder"] = data_path()
        kwargs["output_folder"] = data_path()
        kwargs["model_folder"] = data_path()
        super().__init__(**kwargs)

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times()[-1])
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


class TestOptimizationProblem(TestCase):
    """
    Tests the default methods from OptimizationProblem
    """

    def setUp(self):
        self.problem = Model()
        self.problem.read()
        self.tolerance = 1e-6

    def test_get_timeseries(self):
        timeseries = self.problem.get_timeseries("constant_input")
        expected_times = [-7200, -3600, 0, 3600, 7200, 9800]
        self.assertTrue(np.array_equal(timeseries.times, expected_times))
        expected_values = [1.1, 1.4, 0.9, 1.2, 1.5, 1.7]
        self.assertTrue(np.array_equal(timeseries.values, expected_values))

        timeseries_x = self.problem.get_timeseries("x")
        self.assertTrue(np.array_equal(timeseries_x.times, expected_times))
        expected_values = [3.1, 3.2, 3.3, 3.4, 3.5, 3.6]
        self.assertTrue(np.array_equal(timeseries_x.values, expected_values))

    def test_set_timeseries_with_timeseries(self):
        times = self.problem.io.times_sec
        values = [0.1, 1.1, 2.1, 3.1, 4.1, 5.1]
        self.problem.set_timeseries("newVar", Timeseries(times, values))

        actual_series = self.problem.get_timeseries("newVar")
        self.assertTrue(np.array_equal(actual_series.values, values))
        self.assertTrue(np.array_equal(actual_series.times, times))

        # test if it was actually stored in the internal data store
        _, actual_values = self.problem.io.get_timeseries_sec("newVar")
        self.assertTrue(np.array_equal(actual_values, values))

        # now let's do this again but only give part of the values
        values = [1.1, 2.1, 3.1]

        # with check_consistency=True (default) we should be fine as long
        # as the timeseries times are a subset of the import times
        self.problem.set_timeseries("partialSeries1", Timeseries(times[-3:], values))
        actual_series = self.problem.get_timeseries("partialSeries1")
        self.assertTrue(np.array_equal(actual_series.times, times))
        self.assertTrue(np.array_equal(actual_series.values[-3:], values))
        self.assertTrue(np.all(np.isnan(actual_series.values[:-3])))

        wrong_times = times[-3:].copy()
        wrong_times[-1] -= 1
        with self.assertRaisesRegex(ValueError, "different times"):
            self.problem.set_timeseries("partialSeries2", Timeseries(wrong_times, values))

        # Without the check, we will also get through with wrong times
        self.problem.set_timeseries(
            "partialSeries2", Timeseries(wrong_times, values), check_consistency=False
        )

        actual_series = self.problem.get_timeseries("partialSeries2")
        self.assertTrue(np.array_equal(actual_series.times, times))
        self.assertTrue(np.array_equal(actual_series.values[-3:], values))
        self.assertTrue(np.all(np.isnan(actual_series.values[:-3])))

    def test_set_timeseries_with_array(self):
        times = self.problem.times()
        values = np.random.random(times.shape)
        self.problem.set_timeseries("newVar", values)

        actual_series = self.problem.get_timeseries("newVar")
        forecast_index = bisect.bisect_left(
            self.problem.io.datetimes, self.problem.io.reference_datetime
        )
        self.assertTrue(np.array_equal(actual_series.values[forecast_index:], values))
        self.assertTrue(np.all(np.isnan(actual_series.values[:forecast_index])))

        # with check_consistency=True (default) we should be fine as long
        # as self.times() returns subset of the import times
        orig_times = self.problem.times()
        self.problem._overrule_times = orig_times[1:]
        self.problem.set_timeseries("partialSeries1", values[1:])
        actual_series = self.problem.get_timeseries("partialSeries1")
        self.assertTrue(np.array_equal(actual_series.times, self.problem.io.times_sec))
        self.assertTrue(np.array_equal(actual_series.values[-3:], values[1:]))
        self.assertTrue(np.all(np.isnan(actual_series.values[:-3])))

        with self.assertRaisesRegex(ValueError, "different length"):
            self.problem.set_timeseries("partialSeries1", values)

        wrong_times = orig_times.copy()[1:]
        wrong_times[-1] -= 1
        self.problem._overrule_times = wrong_times
        with self.assertRaisesRegex(ValueError, "different times"):
            self.problem.set_timeseries("partialSeries2", values[1:])

        # Without the check, we will also get through with wrong times
        self.problem.set_timeseries("partialSeries2", values[1:], check_consistency=False)

        actual_series = self.problem.get_timeseries("partialSeries2")
        self.assertTrue(np.array_equal(actual_series.times, self.problem.io.times_sec))
        self.assertTrue(np.array_equal(actual_series.values[-3:], values[1:]))
        self.assertTrue(np.all(np.isnan(actual_series.values[:-3])))

    def test_timeseries_at(self):
        times = self.problem.io.times_sec
        values = times.astype(dtype=np.float64) / 10
        self.problem.set_timeseries("myVar", Timeseries(times, values))
        actual = self.problem.timeseries_at("myVar", times[0])
        self.assertEqual(actual, times[0] / 10)

        actual = self.problem.timeseries_at("myVar", (times[0] + times[1]) / 2)
        self.assertEqual(actual, (values[0] + values[1]) / 2)

    def test_bounds(self):
        bounds = self.problem.bounds()
        self.assertEqual(bounds["x"], (float("-inf"), float("inf")))

        min_u = bounds["u"][0]
        max_u = bounds["u"][1]

        expected_times = [0, 3600, 7200, 9800]
        self.assertTrue(np.array_equal(min_u.times, expected_times))
        self.assertTrue(np.array_equal(max_u.times, expected_times))

        expected_min_values = [0.3, 0.1, 0.4, 0.0]
        self.assertTrue(np.array_equal(min_u.values, expected_min_values))

        expected_max_values = [2.0, 2.4, 2.5, 2.3]
        self.assertTrue(np.array_equal(max_u.values, expected_max_values))

    def test_history(self):
        history = self.problem.history(0)

        expected_times = [-7200, -3600, 0]
        self.assertTrue(np.array_equal(history["x"].times, expected_times))
        self.assertTrue(np.array_equal(history["constant_input"].times, expected_times))

        expected_history_x = [3.1, 3.2, 3.3]
        self.assertTrue(np.array_equal(history["x"].values, expected_history_x))
        expected_history_u = [1.1, 1.4, 0.9]
        self.assertTrue(np.array_equal(history["constant_input"].values, expected_history_u))

    def test_seed(self):
        # add another variable containing some nans
        self.problem.io.set_timeseries_sec(
            "some_missing",
            self.problem.io.times_sec,
            np.array([np.nan, 0.1, 0.2, np.nan, 3.1, np.nan]),
        )
        self.problem.dae_variables["free_variables"].append(ca.MX().sym("some_missing"))

        seed = self.problem.seed(0)
        self.assertTrue(np.array_equal(seed["x"].values, [3.1, 3.2, 3.3, 3.4, 3.5, 3.6]))
        self.assertTrue(np.array_equal(seed["alias"].values, [3.1, 3.2, 3.3, 3.4, 3.5, 3.6]))
        self.assertTrue(np.array_equal(seed["some_missing"].values, [0, 0.1, 0.2, 0, 3.1, 0]))

    def test_constant_inputs(self):
        constant_inputs = self.problem.constant_inputs(0)
        self.assertTrue(
            np.array_equal(constant_inputs["constant_input"].values, [1.1, 1.4, 0.9, 1.2, 1.5, 1.7])
        )


class ModelSubTimes(Model):
    def times(self, variable=None):
        return super().times(variable)[:-1]


class TestOptimizationProblemSubTimes(TestCase):
    def setUp(self):
        self.problem = ModelSubTimes()
        self.problem.read()
        self.tolerance = 1e-6

    def test_set_timeseries_slice(self):
        full_times = self.problem.io.times_sec

        slice_times = self.problem.times()
        slice_values = np.zeros_like(slice_times)

        # Make sure our slice is somewhere in the middle
        self.assertGreater(slice_times[0], full_times[0])
        self.assertLess(slice_times[-1], full_times[-1])

        self.problem.set_timeseries("subslice_timeseries", Timeseries(slice_times, slice_values))

        times, values = self.problem.io.get_timeseries("subslice_timeseries")
        ref_values = [np.nan, np.nan, 0.0, 0.0, 0.0, np.nan]
        np.testing.assert_allclose(values, ref_values, equal_nan=True)


class IOEnsembleModel(Model):
    """Test model for IOMixin ensemble specific bounds."""

    ensemble_specific_bounds = True

    @property
    def ensemble_size(self):
        return 2

    def read(self):
        super().read()

        # Copy all timeseries to the second member, except for u_Min and u_Max.
        # Those we slightly modify for the second member.
        for variable in self.io.get_timeseries_names():
            datetimes, values = self.io.get_timeseries(variable, 0)

            if variable.endswith("_Min"):
                offset = -0.1
            elif variable.endswith("_Max"):
                offset = 0.1
            else:
                offset = 0.0

            self.io.set_timeseries(variable, datetimes, values + offset, ensemble_member=1)


class TestIOMixinEnsembleSpecificBounds(TestCase):
    def setUp(self):
        self.problem = IOEnsembleModel()
        # Call pre() to trigger the read() method and setup io
        self.problem.pre()
        self.tolerance = 1e-9

    def test_io_ensemble_bounds(self):
        expected_times = np.array([0, 3600, 7200, 9800])

        lb_values = np.array([0.3, 0.1, 0.4, 0.0])
        ub_values = np.array([2.0, 2.4, 2.5, 2.3])

        # Ensemble Member 0 - no offset
        expected_lb_values_member_0 = lb_values
        expected_ub_values_member_0 = ub_values
        bounds_member_0 = self.problem.bounds(0)

        lb, ub = bounds_member_0["u"]
        np.testing.assert_array_equal(lb.times, expected_times)
        np.testing.assert_array_equal(ub.times, expected_times)
        np.testing.assert_array_equal(lb.values, expected_lb_values_member_0)
        np.testing.assert_array_equal(ub.values, expected_ub_values_member_0)

        # Ensemble Member 1 - with offset
        expected_lb_values_member_1 = lb_values - 0.1
        expected_ub_values_member_1 = ub_values + 0.1
        bounds_member_1 = self.problem.bounds(1)

        lb, ub = bounds_member_1["u"]
        np.testing.assert_array_equal(lb.times, expected_times)
        np.testing.assert_array_equal(ub.times, expected_times)
        np.testing.assert_array_equal(lb.values, expected_lb_values_member_1)
        np.testing.assert_array_equal(ub.values, expected_ub_values_member_1)
