import logging
from datetime import datetime, timedelta
from unittest import TestCase

import numpy as np
from pymoca.backends.casadi.alias_relation import AliasRelation

from rtctools.data.storage import DataStoreAccessor

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)


class DummyDataStore(DataStoreAccessor):
    @property
    def alias_relation(self):
        return AliasRelation()


class TestDummyDataStore(TestCase):
    def setUp(self):
        self.datastore = DummyDataStore(input_folder="dummyInput", output_folder="dummyOutput")
        self.tolerance = 1e-6

    def test_times(self):
        # Set a reference datetime
        ref_datetime = datetime(2000, 1, 1)
        self.datastore.io.reference_datetime = ref_datetime

        expected_times_sec = np.array([-7200, -3600, 0, 3600, 7200, 9800], dtype=np.float64)
        expected_datetimes = [ref_datetime + timedelta(seconds=x) for x in expected_times_sec]

        self.datastore.io.set_timeseries("dummyVar", expected_datetimes, np.zeros((6,)))

        actual_datetimes = self.datastore.io.datetimes
        self.assertEqual(actual_datetimes, expected_datetimes)

        actual_times = self.datastore.io.times_sec
        self.assertTrue(np.array_equal(actual_times, expected_times_sec))

    def test_timeseries(self):
        # expect a KeyError when getting a timeseries that has not been set
        with self.assertRaises(KeyError):
            self.datastore.io.get_timeseries("someNoneExistentVariable")

        # Set a reference datetime
        ref_datetime = datetime(2000, 1, 1)
        self.datastore.io.reference_datetime = ref_datetime

        # Make a timeseries
        times_sec = np.array([-3600, 0, 7200], dtype=np.float64)
        datetimes = [ref_datetime + timedelta(seconds=x) for x in times_sec]

        expected_values = np.array([3.1, 2.4, 2.5])
        self.datastore.io.set_timeseries("myNewVariable", datetimes, expected_values)
        _, actual_values = self.datastore.io.get_timeseries("myNewVariable")
        self.assertTrue(np.array_equal(actual_values, expected_values))

        # Also check using the seconds interface
        actual_times, actual_values = self.datastore.io.get_timeseries_sec("myNewVariable")
        self.assertTrue(np.array_equal(actual_times, times_sec))
        self.assertTrue(np.array_equal(actual_values, expected_values))

        # Check that we can no longer overwrite the reference datetime,
        # because we called get_timeseries_sec/set_timeseries_sec.
        with self.assertRaisesRegex(
            RuntimeError, "Cannot change reference datetime after times in seconds"
        ):
            self.datastore.io.reference_datetime = datetime(2010, 1, 1)

        # expect a KeyError when getting timeseries for an ensemble member that doesn't exist
        with self.assertRaisesRegex(KeyError, "ensemble_member 1 does not exist"):
            self.datastore.io.get_timeseries("myNewVariable", 1)

        # Set timeseries with times in seconds
        expected_values = np.array([1.1, 1.4, 1.5])
        self.datastore.io.set_timeseries_sec(
            "ensembleVariable", times_sec, expected_values, ensemble_member=1
        )
        with self.assertRaises(KeyError):
            self.datastore.io.get_timeseries("ensembleVariable", 0)
        _, actual_values = self.datastore.io.get_timeseries("ensembleVariable", 1)
        self.assertTrue(np.array_equal(actual_values, expected_values))

        # expect a warning when overwriting a timeseries with check_duplicates=True
        new_values = np.array([2.1, 1.1, 0.1])
        with self.assertLogs(logger, level="WARN") as cm:
            self.datastore.io.set_timeseries(
                "myNewVariable", datetimes, new_values, check_duplicates=True
            )
            self.assertEqual(
                cm.output,
                [
                    "WARNING:rtctools:Time series values for ensemble member 0 and variable "
                    "myNewVariable set twice. Overwriting old values."
                ],
            )
        _, actual_values = self.datastore.io.get_timeseries("myNewVariable")
        self.assertTrue(np.array_equal(actual_values, new_values))

        # By default we expect no warning when verwriting old values
        newest_values = np.array([-0.4, 2.14, 29.1])
        with self.assertLogs(logger, level="WARN") as cm:
            self.datastore.io.set_timeseries("myNewVariable", datetimes, newest_values)
            self.assertEqual(cm.output, [])
            logger.warning(
                "All is well"
            )  # if no log message occurs, assertLogs will throw an AssertionError
        _, actual_values = self.datastore.io.get_timeseries("myNewVariable")
        self.assertTrue(np.array_equal(actual_values, newest_values))

    def test_parameters(self):
        # expect a KeyError when getting a parameter that has not been set
        with self.assertRaises(KeyError):
            self.datastore.io.get_parameter("someNoneExistentParameter")

        self.datastore.io.set_parameter("myNewParameter", 1.4)
        self.assertEqual(self.datastore.io.get_parameter("myNewParameter"), 1.4)
        self.assertEqual(self.datastore.io.parameters()["myNewParameter"], 1.4)

        # expect a KeyError when getting parameters for an ensemble member that doesn't exist
        with self.assertRaises(KeyError):
            self.datastore.io.get_parameter("myNewParameter", 1)
        with self.assertRaises(KeyError):
            self.datastore.io.parameters(1)["myNewParameter"]

        self.datastore.io.set_parameter("ensembleParameter", 1.2, ensemble_member=1)
        with self.assertRaises(KeyError):
            self.datastore.io.get_parameter("ensembleParameter", 0)
        with self.assertRaises(KeyError):
            self.datastore.io.parameters(0)["ensembleParameter"]
        self.assertEqual(self.datastore.io.get_parameter("ensembleParameter", 1), 1.2)
        self.assertEqual(self.datastore.io.parameters(1)["ensembleParameter"], 1.2)

        # expect a warning when overwriting a parameter with check_duplicates=True
        with self.assertLogs(logger, level="WARN") as cm:
            self.datastore.io.set_parameter("myNewParameter", 2.5, check_duplicates=True)
            self.assertEqual(
                cm.output,
                [
                    "WARNING:rtctools:Attempting to set parameter value for ensemble member 0 "
                    "and name myNewParameter twice. Using new value of 2.5."
                ],
            )
        self.assertEqual(self.datastore.io.get_parameter("myNewParameter"), 2.5)
        self.assertEqual(self.datastore.io.parameters()["myNewParameter"], 2.5)

        # By default we expect no warning when overwriting old values
        with self.assertLogs(logger, level="WARN") as cm:
            self.datastore.io.set_parameter("myNewParameter", 2.2)
            self.assertEqual(cm.output, [])
            logger.warning(
                "All is well"
            )  # if no log message occurs, assertLogs will throw an AssertionError
        self.assertEqual(self.datastore.io.get_parameter("myNewParameter"), 2.2)
        self.assertEqual(self.datastore.io.parameters()["myNewParameter"], 2.2)
