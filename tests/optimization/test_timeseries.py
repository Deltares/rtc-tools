import unittest

import casadi as ca
import numpy as np

from rtctools.optimization.timeseries import Timeseries


class TestTimeseries(unittest.TestCase):
    def test_dm(self):
        ts = Timeseries([1, 2, 3], ca.DM([1, 2, 3]))
        self.assertTrue(np.array_equal(ts.values, np.array([1, 2, 3])))
        self.assertEqual(ts.values.dtype, np.float64)

    def test_broadcast_scalar(self):
        ts = Timeseries([1, 2, 3], 4)
        self.assertTrue(np.array_equal(ts.values, np.array([4, 4, 4])))
        self.assertEqual(ts.values.dtype, np.float64)

    def test_broadcast_single_element(self):
        ts = Timeseries([1, 2, 3], [4])
        self.assertTrue(np.array_equal(ts.values, np.array([4, 4, 4])))
        self.assertEqual(ts.values.dtype, np.float64)

    def test_numpy_array(self):
        vals = np.array([1, 2, 3], dtype=np.float64)
        ts = Timeseries([1, 2, 3], vals)
        self.assertTrue(np.array_equal(ts.values, vals))
        self.assertEqual(ts.values.dtype, np.float64)
        self.assertFalse(vals is ts.values)  # Make sure a copy was made

    def test_list(self):
        vals = [1, 2, 3]
        ts = Timeseries([1, 2, 3], vals)
        self.assertTrue(np.array_equal(ts.values, np.array(vals, dtype=np.float64)))
        self.assertEqual(ts.values.dtype, np.float64)

    def test_equal(self):
        ts_int = Timeseries([1, 2, 3], [4, 5, 6])
        ts_float = Timeseries([1, 2, 3], [4.0, 5.0, 6.0])

        ts_diff_values = Timeseries([1, 2, 3], [1, 2, 3])
        ts_diff_times = Timeseries([4, 5, 6], [4, 5, 6])

        self.assertEqual(ts_int, ts_int)
        self.assertEqual(ts_float, ts_float)
        self.assertEqual(ts_int, ts_float)

        self.assertNotEqual(ts_float, ts_diff_times)
        self.assertNotEqual(ts_float, ts_diff_values)
