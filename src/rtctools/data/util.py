from datetime import datetime
from typing import List

import numpy as np


def check_times_are_increasing(times: List[datetime]):
    """Check that time stamps are increasing."""
    for i in range(len(times) - 1):
        if times[i] >= times[i + 1]:
            raise ValueError("Time stamps must be strictly increasing.")


def check_times_are_equidistant(times: List[datetime]):
    """Check that times are eqeuidistant."""
    dt = times[1] - times[0]
    for i in range(len(times) - 1):
        if times[i + 1] - times[i] != dt:
            raise ValueError(
                "Expecting equidistant timeseries, the time step towards "
                "{} is not the same as the time step(s) before. ".format(times[i + 1])
            )


def fill_nan_in_timeseries(times: List[datetime], values: np.ndarray, interp_args: dict = None):
    """Fill in missing values in a timeseries using lienar interpolation.

    :param times:   List of datetimes.
    :param values:  1D array of values with the same length as times.
    :interp_args:   Dict of arguments passed to numpy.interp.

    :returns:       List of values where nans have been replaced with interpolated values.
    """
    if interp_args is None:
        interp_args = {}
    times_sec = np.array([(t - times[0]).total_seconds() for t in times])
    nans = np.isnan(values)
    if all(nans):
        return values
    result = np.interp(times_sec, times_sec[~nans], values[~nans], **interp_args)
    return result
