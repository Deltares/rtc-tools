import logging
import sys
from datetime import datetime

import numpy as np

logger = logging.getLogger("rtctools")


def _boolean_to_nan(data, fname):
    """
    Empty columns are detected as boolean full of "False". We instead want this to be np.nan.
    We cannot distinguish between explicitly desired boolean columns, so instead we convert all
    boolean columns to np.nan, and raise a warning.
    """
    data = data.copy()

    dtypes_in = []
    for i in range(0, len(data.dtype)):
        dtypes_in.append(data.dtype.descr[i])

    convert_to_nan = []
    dtypes_out = []
    for i, name in enumerate(data.dtype.names):
        if dtypes_in[i][1][1] == "b":
            convert_to_nan.append(name)
            dtypes_out.append((dtypes_in[i][0], "<f8"))
        else:
            dtypes_out.append(dtypes_in[i])

    if convert_to_nan:
        logger.warning(
            "Column(s) {} were detected as boolean in '{}'; converting to NaN".format(
                ", ".join([f"'{name}'" for name in convert_to_nan]), fname
            )
        )
        data = data.astype(dtypes_out)
        for name in convert_to_nan:
            data[name] = np.nan

    return data


def _string_to_datetime(string: str | bytes) -> datetime:
    """Convert a string to a datetime object."""
    if isinstance(string, bytes):
        string = string.decode("utf-8")
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


def _string_to_float(string: str | bytes) -> float:
    """Convert a string to a float."""
    if isinstance(string, bytes):
        string = string.decode("utf-8")
    string = string.replace(",", ".")
    return float(string)


def load(fname, delimiter=",", with_time=False):
    """
    Check delimiter of csv and read contents to an array. Assumes no date-time conversion needed.

    :param fname:     Filename.
    :param delimiter: CSV column delimiter.
    :param with_time: Whether the first column is expected to contain time stamps.

    :returns: A named numpy array with the contents of the file.
    """
    c = {}
    if with_time:
        c.update({0: _string_to_datetime})

    # Check delimiter of csv file. If semicolon, check if decimal separator is
    # a comma.
    if delimiter == ";":
        with open(fname, "rb") as csvfile:
            # Read the first line, this should be a header. Count columns by
            # counting separator.
            sample_csvfile = csvfile.readline()
            n_semicolon = sample_csvfile.count(b";")
            # We actually only need one number to evaluate if commas are used as decimal
            # separator, but certain csv writers don't use a decimal when the value has
            # no meaningful decimal(e.g. 12.0 becomes 12) so we read the next 1024 bytes
            # to make sure we catch a number.
            sample_csvfile = csvfile.read(1024)
            # Count the commas
            n_comma_decimal = sample_csvfile.count(b",")
            # If commas are used as decimal separator, we need additional
            # converters.
            if n_comma_decimal:
                c.update({i + len(c): _string_to_float for i in range(1 + n_semicolon - len(c))})

    # Read the csv file and convert to array
    try:
        if len(c):  # Converters exist, so use them.
            try:
                data = np.genfromtxt(
                    fname, delimiter=delimiter, deletechars="", dtype=None, names=True, converters=c
                )
                return _boolean_to_nan(data, fname)
            except (
                np.lib._iotools.ConverterError
            ):  # value does not conform to expected date-time format
                type, value, traceback = sys.exc_info()
                logger.error(f"CSVMixin: converter of csv reader failed on {fname}: {value}")
                raise ValueError(
                    f"CSVMixin: wrong date time or value format in {fname}. "
                    "Should be %Y-%m-%d %H:%M:%S and numerical values everywhere."
                )
        else:
            data = np.genfromtxt(fname, delimiter=delimiter, deletechars="", dtype=None, names=True)
            return _boolean_to_nan(data, fname)
    except ValueError:
        # can occur when delimiter changes after first 1024 bytes of file,
        # or delimiter is not , or ;
        type, value, traceback = sys.exc_info()
        logger.error(f"CSV: Value reader of csv reader failed on {fname}: {value}")
        raise ValueError(
            f"CSV: could not read all values from {fname}. Used delimiter '{delimiter}'. "
            "Please check delimiter (should be ',' or ';' throughout the file) "
            "and if all values are numbers."
        )


def save(fname, data, delimiter=",", with_time=False):
    """
    Write the contents of an array to a csv file.

    :param fname:     Filename.
    :param data:      A named numpy array with the data to write.
    :param delimiter: CSV column delimiter.
    :param with_time: Whether to output the first column of the data as time stamps.
    """
    if with_time:
        data["time"] = [t.strftime("%Y-%m-%d %H:%M:%S") for t in data["time"]]
        fmt = ["%s"] + (len(data.dtype.names) - 1) * ["%f"]
    else:
        fmt = len(data.dtype.names) * ["%f"]

    np.savetxt(
        fname,
        data,
        delimiter=delimiter,
        header=delimiter.join(data.dtype.names),
        fmt=fmt,
        comments="",
    )
