import bisect
import logging
import warnings
from abc import ABCMeta, abstractmethod
from typing import Optional

import casadi as ca
import numpy as np

from rtctools._internal.caching import cached
from rtctools._internal.ensemble_bounds_decorator import ensemble_bounds_check
from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.optimization.timeseries import Timeseries

logger = logging.getLogger("rtctools")


class IOMixin(OptimizationProblem, metaclass=ABCMeta):
    """
    Base class for all IO methods of optimization problems.
    """

    def __init__(self, **kwargs):
        # Call parent class first for default behaviour.
        super().__init__(**kwargs)

        # Additional output variables
        self.__output_timeseries = set()
        self.__equidistant = False

    def pre(self) -> None:
        # Call parent class first for default behaviour.
        super().pre()

        # Call read method to read all input
        self.read()

        # Check equidistancy on read input data
        if self.io.datetimes:
            self.__equidistant = len(set(np.diff(self.io.datetimes))) == 1

    @abstractmethod
    def read(self) -> None:
        """
        Reads input data from files
        """
        pass

    def post(self) -> None:
        # Call parent class first for default behaviour.
        super().post()

        # Call write method to write all output
        self.write()

    @abstractmethod
    def write(self) -> None:
        """
        Writes output data to files
        """
        pass

    def times(self, variable=None) -> np.ndarray:
        """
        Returns the times in seconds from the reference datetime onwards.

        :param variable:
        """
        times_sec = self.io.times_sec
        t_idx = bisect.bisect_left(times_sec, 0.0)
        return times_sec[t_idx:]

    @property
    def equidistant(self):
        return self.__equidistant

    @property
    def ensemble_size(self):
        return self.io.ensemble_size

    def get_timeseries(self, variable: str, ensemble_member: int = 0) -> Timeseries:
        return Timeseries(*self.io.get_timeseries_sec(variable, ensemble_member))

    def set_timeseries(
        self,
        variable: str,
        timeseries: Timeseries,
        ensemble_member: int = 0,
        output: bool = True,
        check_consistency: bool = True,
    ):
        def stretch_values(values, t_pos):
            # Construct a values range with preceding and possibly following nans
            new_values = np.full(self.io.times_sec.shape, np.nan)
            new_values[t_pos : t_pos + len(values)] = values
            return new_values

        if output:
            self.__output_timeseries.add(variable)

        if isinstance(timeseries, Timeseries):
            if len(timeseries.values) != len(timeseries.times):
                raise ValueError(
                    "IOMixin: Trying to set timeseries {} with times and values that are of "
                    "different length (lengths of {} and {}, respectively).".format(
                        variable, len(timeseries.times), len(timeseries.values)
                    )
                )

            timeseries_times_sec = self.io.times_sec

            if not np.array_equal(timeseries_times_sec, timeseries.times):
                if check_consistency:
                    if not set(timeseries_times_sec).issuperset(timeseries.times):
                        raise ValueError(
                            "IOMixin: Trying to set timeseries {} with different times "
                            "(in seconds) than the imported timeseries. Please make sure the "
                            "timeseries covers all timesteps of the longest "
                            "imported timeseries.".format(variable)
                        )

                # Determine position of first times of added timeseries within the
                # import times. For this we assume that both time ranges are ordered,
                # and that the times of the added series is a subset of the import
                # times.
                t_pos = bisect.bisect_left(timeseries_times_sec, timeseries.times[0])

                # Construct a new values range with length of self.io.get_times()
                values = stretch_values(timeseries.values, t_pos)
            else:
                values = timeseries.values

        else:
            timeseries_times_sec = self.io.times_sec

            if check_consistency:
                if len(self.times()) != len(timeseries):
                    raise ValueError(
                        "IOMixin: Trying to set values for {} with a different "
                        "length ({}) than the forecast length ({}).".format(
                            variable, len(timeseries), len(self.times())
                        )
                    )
                elif not set(timeseries_times_sec).issuperset(self.times()):
                    raise ValueError(
                        "IOMixin: Trying to set timeseries {} with different times "
                        "(in seconds) than the imported timeseries. Please make sure the "
                        "timeseries covers all timesteps of the longest "
                        "imported timeseries.".format(variable)
                    )

            # If times is not supplied with the timeseries, we add the
            # forecast times range to a new Timeseries object. Hereby
            # we assume that the supplied values stretch from T0 to end.
            t_pos = bisect.bisect_left(timeseries_times_sec, self.initial_time)

            # Construct a new values range with length of self.io.get_times()
            values = stretch_values(timeseries, t_pos)

        self.io.set_timeseries(variable, self.io.datetimes, values, ensemble_member)

    def min_timeseries_id(self, variable: str) -> str:
        """
        Returns the name of the lower bound timeseries for the specified variable.

        :param variable: Variable name.
        """
        return "_".join((variable, "Min"))

    def max_timeseries_id(self, variable: str) -> str:
        """
        Returns the name of the upper bound timeseries for the specified variable.

        :param variable: Variable name.
        """
        return "_".join((variable, "Max"))

    @cached
    @ensemble_bounds_check
    def bounds(self, ensemble_member: Optional[int] = None):
        bounds = (
            super().bounds(ensemble_member) if self.ensemble_specific_bounds else super().bounds()
        )

        ensemble_member = ensemble_member if self.ensemble_specific_bounds else 0

        io_times = self.io.times_sec
        t_pos = bisect.bisect_left(io_times, self.initial_time)

        # Load bounds from timeseries
        for variable in self.dae_variables["free_variables"]:
            variable_name = variable.name()

            m, M = None, None

            timeseries_id = self.min_timeseries_id(variable_name)
            try:
                _, values = self.io.get_timeseries_sec(timeseries_id, ensemble_member)
                m = values[t_pos:]
            except KeyError:
                pass
            else:
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug("Read lower bound for variable {}".format(variable_name))

            timeseries_id = self.max_timeseries_id(variable_name)
            try:
                _, values = self.io.get_timeseries_sec(timeseries_id, ensemble_member)
                M = values[t_pos:]
            except KeyError:
                pass
            else:
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug("Read upper bound for variable {}".format(variable_name))

            # Replace NaN with +/- inf, and create Timeseries objects
            if m is not None:
                m[np.isnan(m)] = np.finfo(m.dtype).min
                m = Timeseries(io_times[t_pos:], m)
            if M is not None:
                M[np.isnan(M)] = np.finfo(M.dtype).max
                M = Timeseries(io_times[t_pos:], M)

            # Store
            if m is not None or M is not None:
                bounds[variable_name] = (m, M)
        return bounds

    @cached
    def history(self, ensemble_member):
        # Load history
        history = super().history(ensemble_member)

        end_index = bisect.bisect_left(self.io.times_sec, self.initial_time) + 1

        variable_list = (
            self.dae_variables["states"]
            + self.dae_variables["algebraics"]
            + self.dae_variables["control_inputs"]
            + self.dae_variables["constant_inputs"]
        )

        for variable in variable_list:
            variable = variable.name()
            try:
                times, values = self.io.get_timeseries_sec(variable, ensemble_member)
                history[variable] = Timeseries(times[:end_index], values[:end_index])
            except KeyError:
                pass
            else:
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug("IOMixin: Read history for state {}".format(variable))
        return history

    @cached
    def seed(self, ensemble_member):
        # Call parent class first for default values.
        seed = super().seed(ensemble_member)

        # Load seeds
        for variable in self.dae_variables["free_variables"]:
            variable = variable.name()
            try:
                s = Timeseries(*self.io.get_timeseries_sec(variable, ensemble_member))
            except KeyError:
                pass
            else:
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug("IOMixin: Seeded free variable {}".format(variable))
                # A seeding of NaN means no seeding
                s.values[np.isnan(s.values)] = 0.0
                seed[variable] = s
        return seed

    @cached
    def parameters(self, ensemble_member):
        # Call parent class first for default values.
        parameters = super().parameters(ensemble_member)

        for parameter, value in self.io.parameters(ensemble_member).items():
            parameters[parameter] = value

        # Done
        return parameters

    @cached
    def constant_inputs(self, ensemble_member):
        # Call parent class first for default values.
        constant_inputs = super().constant_inputs(ensemble_member)

        # Load inputs from timeseries
        for variable in self.dae_variables["constant_inputs"]:
            variable = variable.name()
            try:
                timeseries = Timeseries(*self.io.get_timeseries_sec(variable, ensemble_member))
            except KeyError:
                pass
            else:
                inds = timeseries.times >= self.initial_time
                if np.any(np.isnan(timeseries.values[inds])):
                    raise Exception("IOMixin: Constant input {} contains NaN".format(variable))
                constant_inputs[variable] = timeseries
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug("IOMixin: Read constant input {}".format(variable))
        return constant_inputs

    def timeseries_at(self, variable, t, ensemble_member=0):
        return self.interpolate(t, *self.io.get_timeseries_sec(variable, ensemble_member))

    @property
    def output_variables(self):
        variables = super().output_variables.copy()
        variables.extend([ca.MX.sym(variable) for variable in self.__output_timeseries])
        return variables

    def get_forecast_index(self):
        """
        Deprecated, use `io.reference_datetime` and `io.datetimes`, or override behavior using
        :py:meth:`OptimizationProblem.times` and/or :py:attr:`OptimizationProblem.initial_time`.
        """
        warnings.warn(
            "get_forecast_index() is deprecated and will be removed in the future",
            FutureWarning,
            stacklevel=1,
        )
        return bisect.bisect_left(self.io.datetimes, self.io.reference_datetime)
