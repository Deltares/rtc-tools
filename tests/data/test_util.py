"""Module for testing data processing utilities."""
from datetime import datetime
from pathlib import Path

import numpy as np
from rtctools.data.util import (
    check_times_are_equidistant,
    check_times_are_increasing,
    fill_nan_in_timeseries,
)
from test_case import TestCase

DATA_DIR = Path(__file__).parent / "data" / "timeseries"


class TestUtil(TestCase):
    def test_check_times_are_equidistant(self):
        """Test checking if a timeseries is equidistant."""
        times = [datetime(2020, 1, 1, 0, 0, sec) for sec in [1, 2, 3]]
        check_times_are_equidistant(times)
        times = [datetime(2020, 1, 1, 0, 0, sec) for sec in [1, 2, 4]]
        with self.assertRaises(ValueError):
            check_times_are_equidistant(times)

    def test_check_timeseries_is_increasing(self):
        """Test checking times are strictly increasing."""
        times = [datetime(2020, 1, 1, 0, 0, sec) for sec in [1, 2, 3]]
        check_times_are_increasing(times)
        times = [datetime(2020, 1, 1, 0, 0, sec) for sec in [1, 2, 2]]
        with self.assertRaises(ValueError):
            check_times_are_increasing(times)

    def test_fill_nan_in_timeseries(self):
        """Test filling nan values of a timeseries."""
        del self
        times = [datetime(2020, 1, 1, 0, 0, sec) for sec in range(5)]
        values = np.array([np.nan, 1.0, np.nan, 3.0, np.nan])
        result = fill_nan_in_timeseries(times, values)
        ref_result = np.array([1.0, 1.0, 2.0, 3.0, 3.0])
        np.testing.assert_almost_equal(result, ref_result)
        values = np.array([np.nan, 1.0, np.nan, np.nan, np.nan])
        result = fill_nan_in_timeseries(times, values)
        ref_result = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        np.testing.assert_almost_equal(result, ref_result)
        values = np.array([np.nan, np.nan, np.nan, np.nan, np.nan])
        result = fill_nan_in_timeseries(times, values)
        assert all(np.isnan(result))
