from datetime import timedelta
import numpy as np
import logging
import bisect
import os

import rtctools.data.csv as csv

from simulation_problem import SimulationProblem

logger = logging.getLogger("rtctools")


class CSVMixin(SimulationProblem):
    """
    Adds reading and writing of CSV timeseries and parameters to your simulation problem.

    During preprocessing, files named ``timeseries_import.csv``, ``initial_state.csv``, and ``parameters.csv`` are read from the ``input`` subfolder.

    During postprocessing, a file named ``timeseries_export.csv`` is written to the ``output`` subfolder.

    In ensemble mode, a file named ``ensemble.csv`` is read from the ``input`` folder.  This file contains two columns.
    The first column gives the name of the ensemble member, and the second column its probability.  Furthermore, the other XML files
    appear one level deeper inside the filesystem hierarchy, inside subfolders with the names of the ensemble members.

    :cvar csv_delimiter:           Column delimiter used in CSV files.  Default is ``,``.
    :cvar csv_validate_timeseries: Check consistency of timeseries.  Default is ``True``.
    """

    #: Column delimiter used in CSV files
    csv_delimiter = ','

    #: Check consistency of timeseries
    csv_validate_timeseries = True

    def __init__(self, **kwargs):
        # Check arguments
        assert('input_folder' in kwargs)
        assert('output_folder' in kwargs)

        # Save arguments
        self._input_folder = kwargs['input_folder']
        self._output_folder = kwargs['output_folder']

        # Call parent class first for default behaviour.
        super().__init__(**kwargs)

    def pre(self):
        # Call parent class first for default behaviour.
        super().pre()

        # Helper function to check if initiale state array actually defines
        # only the initial state
        def check_initial_state_array(initial_state):
            """
            Check length of initial state array, throw exception when larger than 1.
            """
            if initial_state.shape:
                raise Exception("CSVMixin: Initial state file {} contains more than one row of data. Please remove the data row(s) that do not describe the initial state.".format(
                    os.path.join(self._input_folder, 'initial_state.csv')))

        # Read CSV files
        _timeseries = csv.load(os.path.join(
            self._input_folder, 'timeseries_import.csv'), delimiter=self.csv_delimiter, with_time=True)
        self._timeseries_times = _timeseries[_timeseries.dtype.names[0]]
        self._timeseries = {key: np.asarray(_timeseries[key], dtype=np.float64) for key in _timeseries.dtype.names[1:]}
        logger.debug("CSVMixin: Read timeseries.")

        try:
            _parameters = csv.load(os.path.join(
                self._input_folder, 'parameters.csv'), delimiter=self.csv_delimiter)
            logger.debug("CSVMixin: Read parameters.")
            self._parameters = {key: float(_parameters[key]) for key in _parameters.dtype.names}
        except IOError:
            self._parameters = {}

        try:
            _initial_state = csv.load(os.path.join(
                self._input_folder, 'initial_state.csv'), delimiter=self.csv_delimiter)
            logger.debug("CSVMixin: Read initial state.")
            check_initial_state_array(_initial_state)
            self._initial_state = {key: float(_initial_state[key]) for key in _initial_state.dtype.names}
        except IOError:
            self._initial_state = {}

        self._timeseries_times_sec = self._datetime_to_sec(
            self._timeseries_times)

        # Timestamp check
        if self.csv_validate_timeseries:
            for i in range(len(self._timeseries_times_sec) - 1):
                if self._timeseries_times_sec[i] >= self._timeseries_times_sec[i + 1]:
                    raise Exception(
                        'CSVMixin: Time stamps must be strictly increasing.')

        self._dt = self._timeseries_times_sec[1] - self._timeseries_times_sec[0]

        # Check if the timeseries are truly equidistant
        if self.csv_validate_timeseries:
            for i in range(len(self._timeseries_times_sec) - 1):
                if self._timeseries_times_sec[i + 1] - self._timeseries_times_sec[i] != self._dt:
                    raise Exception('CSVMixin: Expecting equidistant timeseries, the time step towards {} is not the same as the time step(s) before. Set equidistant=False if this is intended.'.format(
                        self._timeseries_times[i + 1]))

    def initialize(self, config_file=None):
        # Set up experiment
        self.setup_experiment(0, self._timeseries_times_sec[-1], self._dt)

        # Load parameters from parameter config
        self._parameter_variables = set(self.get_parameter_variables())

        logger.debug("Model parameters are {}".format(self._parameter_variables))

        for parameter, value in self._parameters.iteritems():
            if parameter in self._parameter_variables:
                logger.debug("Setting parameter {} = {}".format(parameter, value))

                self.set_var(parameter, value)

        # Load input variable names
        self._input_variables = set(self.get_input_variables().keys())

        # Set initial states
        for variable, value in self._initial_state.iteritems():
            if variable in self._input_variables:
                if variable in self._timeseries:
                    logger.warning("Entry {} in initial_state.csv was also found in timeseries_import.csv.".format(variable))
                self.set_var(variable, value)
            else:
                logger.warning("Entry {} in initial_state.csv is not an input variable.".format(variable))

        logger.debug("Model inputs are {}".format(self._input_variables))

        # Set initial input values
        for variable, timeseries in self._timeseries.iteritems():
            if variable in self._input_variables:
                value = timeseries[0]
                if np.isfinite(value):
                    self.set_var(variable, value)

        # Empty output
        self._output_variables = set(self.get_output_variables().keys())
        n_times = len(self._timeseries_times_sec)
        self._output = {variable : np.full(n_times, np.nan) for variable in self._output_variables}

        # Call super, which will also initialize the model itself
        super().initialize(config_file)

        # Extract consistent t0 values
        for variable in self._output_variables:
            self._output[variable][0] = self.get_var(variable)

    def update(self, dt):
        # Time step
        if dt < 0:
            dt = self._dt

        # Current time stamp
        t = self.get_current_time()

        # Get current time index
        t_idx = bisect.bisect_left(self._timeseries_times_sec, t + dt)

        # Set input values
        for variable, timeseries in self._timeseries.iteritems():
            if variable in self._input_variables:
                value = timeseries[t_idx]
                if np.isfinite(value):
                    self.set_var(variable, value)

        # Call super
        super().update(dt)

        # Extract results
        for variable in self._output_variables:
            self._output[variable][t_idx] = self.get_var(variable)

    def post(self):
        # Call parent class first for default behaviour.
        super().post()

         # Write output
        names = ['time'] + sorted(set(self._output.keys()))
        formats = ['O'] + (len(names) - 1) * ['f8']
        dtype = dict(names=names, formats=formats)
        data = np.zeros(len(self._timeseries_times), dtype=dtype)
        data['time'] = self._timeseries_times
        for variable, values in self._output.iteritems():
            data[variable] = values

        fname = os.path.join(self._output_folder, 'timeseries_export.csv')
        csv.save(fname, data, delimiter=self.csv_delimiter, with_time=True)

    def _datetime_to_sec(self, d):
        # Return the date/timestamps in seconds since t0.
        if hasattr(d, '__iter__'):
            return np.array([(t - self._timeseries_times[0]).total_seconds() for t in d])
        else:
            return (d - self._timeseries_times[0]).total_seconds()

    def _sec_to_datetime(self, s):
        # Return the date/timestamps in seconds since t0 as datetime objects.
        if hasattr(s, '__iter__'):
            return [self._timeseries_times[0] + timedelta(seconds=t) for t in s]
        else:
            return self._timeseries_times[0] + timedelta(seconds=s)

    def timeseries_at(self, variable, t):
        """
        Return the value of a time series at the given time.

        :param variable: Variable name.
        :param t: Time.

        :returns: The interpolated value of the time series.

        :raises: KeyError
        """
        values = self._timeseries[variable]
        t_idx = bisect.bisect_left(self._timeseries_times_sec, t)
        if self._timeseries_times_sec[t_idx] == t:
            return values[t_idx]
        else:
            return np.interp1d(t, self._timeseries_times_sec, values)
