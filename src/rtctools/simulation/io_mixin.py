import bisect
import logging
from abc import ABCMeta, abstractmethod
from math import isfinite

import numpy as np

from rtctools._internal.alias_tools import AliasDict
from rtctools._internal.caching import cached
from rtctools.simulation.simulation_problem import SimulationProblem

logger = logging.getLogger("rtctools")


class IOMixin(SimulationProblem, metaclass=ABCMeta):
    """
    Base class for all IO methods of optimization problems.
    """

    def __init__(self, **kwargs):
        # Call parent class first for default behaviour.
        super().__init__(**kwargs)

        self._simulation_times = []

        self.__first_update_call = True

    def pre(self) -> None:
        # Call read method to read all input
        self.read()

        self._simulation_times = []

    @abstractmethod
    def read(self) -> None:
        """
        Reads input data from files, storing it in the internal data store through the various set
        or add methods
        """
        pass

    def post(self) -> None:
        # Call write method to write all output
        self.write()

    @abstractmethod
    def write(self) -> None:
        """
        Writes output data to files, getting the data from the data store through the various get
        methods
        """
        pass

    def initialize(self, config_file=None):
        # Set up experiment
        timeseries_import_times = self.io.times_sec
        self.__dt = timeseries_import_times[1] - timeseries_import_times[0]
        self.setup_experiment(0, timeseries_import_times[-1], self.__dt)

        parameter_variables = set(self.get_parameter_variables())

        logger.debug("Model parameters are {}".format(parameter_variables))

        for parameter, value in self.io.parameters().items():
            if parameter in parameter_variables:
                logger.debug("IOMixin: Setting parameter {} = {}".format(parameter, value))
                self.set_var(parameter, value)

        # Load input variable names
        self.__input_variables = set(self.get_input_variables().keys())

        # Set input values
        t_idx = bisect.bisect_left(timeseries_import_times, 0.0)
        self.__set_input_variables(t_idx)

        logger.debug("Model inputs are {}".format(self.__input_variables))

        # Set first timestep
        self._simulation_times.append(self.get_current_time())

        # Empty output
        self._io_output_variables = self.get_output_variables()
        self._io_output = AliasDict(self.alias_relation)

        # Call super, which will also initialize the model itself
        super().initialize(config_file)

        # Extract consistent t0 values
        for variable in self._io_output_variables:
            self._io_output[variable] = [self.get_var(variable)]

    def __set_input_variables(self, t_idx, use_cache=False):
        if not use_cache:
            self.__cache_loop_timeseries = {}

            timeseries_names = set(self.io.get_timeseries_names(0))
            for v in self.get_input_variables():
                if v in timeseries_names:
                    _, values = self.io.get_timeseries_sec(v)
                    self.__cache_loop_timeseries[v] = values

        for variable, values in self.__cache_loop_timeseries.items():
            value = values[t_idx]
            if isfinite(value):
                self.set_var(variable, value)
            else:
                logger.debug(
                    "IOMixin: Found bad value {} at index [{}] "
                    "in timeseries aliased to input {}".format(value, t_idx, variable)
                )

    def update(self, dt):
        # Time step
        if dt < 0:
            dt = self.__dt

        # Current time stamp
        t = self.get_current_time()
        self._simulation_times.append(t + dt)

        # Get current time index
        t_idx = bisect.bisect_left(self.io.times_sec, t + dt)

        # Set input values
        self.__set_input_variables(t_idx, not self.__first_update_call)

        # Call super
        super().update(dt)

        # Extract results
        for variable, values in self._io_output.items():
            values.append(self.get_var(variable))

        self.__first_update_call = False

    def extract_results(self):
        """
        Extracts the results of output

        :returns: An AliasDict of output variables and results array format.
        """
        io_outputs_arrays = self._io_output.copy()
        for k in io_outputs_arrays.keys():
            io_outputs_arrays[k] = np.array(io_outputs_arrays[k])

        return io_outputs_arrays

    @cached
    def parameters(self):
        """
        Return a dictionary of parameters, including parameters in the input files files.

        :returns: Dictionary of parameters
        """
        # Call parent class first for default values.
        parameters = super().parameters()

        # Load parameters from input files (stored in internal data store)
        for parameter_name, value in self.io.parameters().items():
            parameters[parameter_name] = value

        if logger.getEffectiveLevel() == logging.DEBUG:
            for parameter_name in self.io.parameters().keys():
                logger.debug("IOMixin: Read parameter {}".format(parameter_name))

        return parameters

    def times(self, variable=None):
        """
        Return a list of all the timesteps in seconds.

        :param variable: Variable name.

        :returns: List of all the timesteps in seconds.
        """
        idx = bisect.bisect_left(self.io.datetimes, self.io.reference_datetime)
        return self.io.times_sec[idx:]

    def timeseries_at(self, variable, t):
        """
        Return the value of a time series at the given time.

        :param variable: Variable name.
        :param t: Time.

        :returns: The interpolated value of the time series.

        :raises: KeyError
        """
        timeseries_times_sec, values = self.io.get_timeseries_sec(variable)
        t_idx = bisect.bisect_left(timeseries_times_sec, t)
        if timeseries_times_sec[t_idx] == t:
            return values[t_idx]
        else:
            return np.interp(t, timeseries_times_sec, values)
