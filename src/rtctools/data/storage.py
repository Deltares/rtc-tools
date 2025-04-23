import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple, Union

import numpy as np

from rtctools._internal.alias_tools import AliasDict, AliasRelation

logger = logging.getLogger("rtctools")


class DataStoreAccessor(metaclass=ABCMeta):
    """
    Base class for all problems.
    Adds an internal data store where timeseries and parameters can be stored.
    Access to the internal data store is always done through the io accessor.

    :cvar timeseries_import_basename:
        Import file basename. Default is ``timeseries_import``.
    :cvar timeseries_export_basename:
        Export file basename. Default is ``timeseries_export``.
    """

    #: Import file basename
    timeseries_import_basename = "timeseries_import"
    #: Export file basename
    timeseries_export_basename = "timeseries_export"

    def __init__(self, **kwargs):
        # Save arguments
        self._input_folder = kwargs["input_folder"] if "input_folder" in kwargs else "input"
        self._output_folder = kwargs["output_folder"] if "output_folder" in kwargs else "output"

        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug("Expecting input files to be located in '" + self._input_folder + "'.")
            logger.debug("Writing output files to '" + self._output_folder + "'.")

        self.io = DataStore(self)

    @property
    @abstractmethod
    def alias_relation(self) -> AliasRelation:
        raise NotImplementedError


class DataStore:
    """
    DataStore class used by the DataStoreAccessor.
    Contains all methods needed to access the internal data store.
    """

    def __init__(self, accessor):
        self.__accessor = accessor

        # Should all be set by subclass via setters
        self.__reference_datetime = None
        self.__timeseries_datetimes = None
        self.__timeseries_times_sec = None
        self.__timeseries_values = [AliasDict(self.__accessor.alias_relation)]
        self.__parameters = [AliasDict(self.__accessor.alias_relation)]

        self.__reference_datetime_fixed = False

        self.__ensemble_size = 1

    @property
    def reference_datetime(self):
        return self.__reference_datetime

    @reference_datetime.setter
    def reference_datetime(self, value):
        if self.__reference_datetime_fixed and value != self.__reference_datetime:
            raise RuntimeError(
                "Cannot change reference datetime after times in seconds has been requested."
            )
        self.__reference_datetime = value

    @property
    def ensemble_size(self):
        return self.__ensemble_size

    def __update_ensemble_size(self, ensemble_size):
        while ensemble_size > len(self.__timeseries_values):
            self.__timeseries_values.append(AliasDict(self.__accessor.alias_relation))

        while ensemble_size > len(self.__parameters):
            self.__parameters.append(AliasDict(self.__accessor.alias_relation))

        assert len(self.__parameters) == len(self.__timeseries_values)
        assert len(self.__parameters) == ensemble_size

        self.__ensemble_size = ensemble_size

    @property
    def datetimes(self) -> List[datetime]:
        """
        Returns the timeseries times in seconds.

        :returns: timeseries datetimes, or None if there has been no call
                  to :py:meth:`set_timeseries`.
        """
        return self.__timeseries_datetimes.copy()

    @property
    def times_sec(self) -> np.ndarray:
        """
        Returns the timeseries times in seconds.

        Note that once this method is called, it is no longer allowed to
        change :py:attr:`reference_datetime`.

        :returns: timeseries times in seconds.
        """
        self._datetimes_to_seconds()

        return self.__timeseries_times_sec

    def _datetimes_to_seconds(self):
        if self.__reference_datetime_fixed:
            pass
        else:
            # Currently we only allow a reference datetime that exists in the
            # timeseries datetimes. That way we can guarantee that we have
            # "0.0" as one of our times in seconds. This restriction may be
            # loosened in the future.
            if self.reference_datetime not in self.__timeseries_datetimes:
                raise Exception(
                    "Reference datetime {} should be equal to "
                    "one of the timeseries datetimes {}".format(
                        self.reference_datetime, self.__timeseries_datetimes
                    )
                )
            self.__timeseries_times_sec = self.datetime_to_sec(
                self.__timeseries_datetimes, self.reference_datetime
            )
            self.__timeseries_times_sec.flags.writeable = False
            self.__reference_datetime_fixed = True

    def set_timeseries(
        self,
        variable: str,
        datetimes: Iterable[datetime],
        values: np.ndarray,
        ensemble_member: int = 0,
        check_duplicates: bool = False,
    ) -> None:
        """
        Stores input time series values in the internal data store.

        :param variable:         Variable name.
        :param datetimes:        Times as datetime objects.
        :param values:           The values to be stored.
        :param ensemble_member:  The ensemble member index.
        :param check_duplicates: If True, a warning will be given when overwriting values.
                                 If False, existing values are silently overwritten with new values.
        """
        datetimes = list(datetimes)

        if not isinstance(datetimes[0], datetime):
            raise TypeError("DateStore.set_timeseries() only support datetimes")

        if self.__timeseries_datetimes is not None and datetimes != self.__timeseries_datetimes:
            raise RuntimeError(
                "Attempting to overwrite the input time series datetimes with different values. "
                "Please ensure all input time series have the same datetimes."
            )
        self.__timeseries_datetimes = datetimes

        if len(self.__timeseries_datetimes) != len(values):
            raise ValueError(
                "Length of values ({}) must be the same as length of datetimes ({})".format(
                    len(values), len(self.__timeseries_datetimes)
                )
            )

        if ensemble_member >= self.__ensemble_size:
            self.__update_ensemble_size(ensemble_member + 1)

        if check_duplicates and variable in self.__timeseries_values[ensemble_member].keys():
            logger.warning(
                "Time series values for ensemble member {} and variable {} set twice. "
                "Overwriting old values.".format(ensemble_member, variable)
            )

        self.__timeseries_values[ensemble_member][variable] = values

    def get_timeseries(
        self, variable: str, ensemble_member: int = 0
    ) -> Tuple[List[datetime], np.ndarray]:
        """
        Looks up the time series in the internal data store.

        :return a tuple (datetimes, values)
        """
        if ensemble_member >= self.__ensemble_size:
            raise KeyError("ensemble_member {} does not exist".format(ensemble_member))
        return self.__timeseries_datetimes, self.__timeseries_values[ensemble_member][variable]

    def get_timeseries_names(self, ensemble_member: int = 0) -> Iterable[str]:
        return self.__timeseries_values[ensemble_member].keys()

    def set_timeseries_sec(
        self,
        variable: str,
        times_in_sec: np.ndarray,
        values: np.ndarray,
        ensemble_member: int = 0,
        check_duplicates: bool = False,
    ) -> None:
        """
        Stores input time series values in the internal data store.

        Note that once this method is called, it is no longer allowed to
        change :py:attr:`reference_datetime`.

        :param variable:         Variable name.
        :param times_in_sec:     The times in seconds.
        :param values:           The values to be stored.
        :param ensemble_member:  The ensemble member index.
        :param check_duplicates: If True, a warning will be given when overwriting values.
                                 If False, existing values are silently overwritten with new values.
        """
        self._datetimes_to_seconds()

        if self.reference_datetime is None:
            raise RuntimeError("Cannot use times in seconds before reference datetime is set.")

        if self.__timeseries_times_sec is not None and not np.array_equal(
            times_in_sec, self.__timeseries_times_sec
        ):
            raise RuntimeError(
                "Attempting to overwrite the input time series times with different values. "
                "Please ensure all input time series have the same times."
            )

        if len(self.__timeseries_datetimes) != len(values):
            raise ValueError(
                "Length of values ({}) must be the same as length of times ({})".format(
                    len(values), len(self.__timeseries_datetimes)
                )
            )

        if ensemble_member >= self.__ensemble_size:
            self.__update_ensemble_size(ensemble_member + 1)

        if check_duplicates and variable in self.__timeseries_values[ensemble_member].keys():
            logger.warning(
                "Time series values for ensemble member {} and variable {} set twice. "
                "Overwriting old values.".format(ensemble_member, variable)
            )

        self.__timeseries_values[ensemble_member][variable] = values

    def get_timeseries_sec(
        self, variable: str, ensemble_member: int = 0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Looks up the time series in the internal data store.

        Note that once this method is called, it is no longer allowed to
        change :py:attr:`reference_datetime`.

        :return a tuple (times, values)
        """
        self._datetimes_to_seconds()

        if ensemble_member >= self.__ensemble_size:
            raise KeyError("ensemble_member {} does not exist".format(ensemble_member))
        return self.__timeseries_times_sec, self.__timeseries_values[ensemble_member][variable]

    def set_parameter(
        self,
        parameter_name: str,
        value: float,
        ensemble_member: int = 0,
        check_duplicates: bool = False,
    ) -> None:
        """
        Stores the parameter value in the internal data store.

        :param parameter_name:   Parameter name.
        :param value:            The values to be stored.
        :param ensemble_member:  The ensemble member index.
        :param check_duplicates: If True, a warning will be given when overwriting values.
                                 If False, existing values are silently overwritten with new values.
        """
        if ensemble_member >= self.__ensemble_size:
            self.__update_ensemble_size(ensemble_member + 1)

        if check_duplicates and parameter_name in self.__parameters[ensemble_member].keys():
            logger.warning(
                "Attempting to set parameter value for ensemble member {} and name {} twice. "
                "Using new value of {}.".format(ensemble_member, parameter_name, value)
            )

        self.__parameters[ensemble_member][parameter_name] = value

    def get_parameter(self, parameter_name: str, ensemble_member: int = 0) -> float:
        """
        Looks up the parameter value in the internal data store.
        """
        if ensemble_member >= self.__ensemble_size:
            raise KeyError("ensemble_member {} does not exist".format(ensemble_member))
        return self.__parameters[ensemble_member][parameter_name]

    def parameters(self, ensemble_member: int = 0) -> AliasDict:
        """
        Returns an AliasDict of parameters to its values for the specified ensemble member.
        """
        if ensemble_member >= self.__ensemble_size:
            self.__update_ensemble_size(ensemble_member + 1)
        return self.__parameters[ensemble_member]

    @staticmethod
    def datetime_to_sec(
        d: Union[Iterable[datetime], datetime], t0: datetime
    ) -> Union[np.ndarray, float]:
        """
        Returns the date/timestamps in seconds since t0.

        :param d:  Iterable of datetimes or a single datetime object.
        :param t0: Reference datetime.
        """
        if hasattr(d, "__iter__"):
            return np.array([(t - t0).total_seconds() for t in d])
        else:
            return (d - t0).total_seconds()

    @staticmethod
    def sec_to_datetime(
        s: Union[Iterable[float], float], t0: datetime
    ) -> Union[List[datetime], datetime]:
        """
        Return the date/timestamps in seconds since t0 as datetime objects.

        :param s:  Iterable of ints or a single int (number of seconds before or after t0).
        :param t0: Reference datetime.
        """
        if hasattr(s, "__iter__"):
            return [t0 + timedelta(seconds=t) for t in s]
        else:
            return t0 + timedelta(seconds=s)
