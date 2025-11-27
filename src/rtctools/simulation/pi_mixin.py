import logging
from datetime import timedelta

import numpy as np

import rtctools.data.pi as pi
import rtctools.data.rtc as rtc
from rtctools.simulation.io_mixin import IOMixin

logger = logging.getLogger("rtctools")


class PIMixin(IOMixin):
    """
    Adds `Delft-FEWS Published Interface
    <https://publicwiki.deltares.nl/display/FEWSDOC/The+Delft-Fews+Published+Interface>`_
    I/O to your simulation problem.

    During preprocessing, files named ``rtcDataConfig.xml``, ``timeseries_import.xml``,
    and``rtcParameterConfig.xml`` are read from the ``input`` subfolder.  ``rtcDataConfig.xml``
    maps tuples of FEWS identifiers, including location and parameter ID, to RTC-Tools time series
    identifiers.

    During postprocessing, a file named ``timeseries_export.xml`` is written to the ``output``
    subfolder.

    :cvar pi_binary_timeseries: Whether to use PI binary timeseries format.  Default is ``False``.
    :cvar pi_parameter_config_basenames:
        List of parameter config file basenames to read. Default is [``rtcParameterConfig``].
    :cvar pi_check_for_duplicate_parameters:
        Check if duplicate parameters are read. Default is ``True``.
    :cvar pi_validate_timeseries: Check consistency of timeseries.  Default is ``True``.
    """

    #: Whether to use PI binary timeseries format
    pi_binary_timeseries = False

    #: Location of rtcParameterConfig files
    pi_parameter_config_basenames = ["rtcParameterConfig"]

    #: Check consistency of timeseries
    pi_validate_timeseries = True

    #: Check for duplicate parameters
    pi_check_for_duplicate_parameters = True

    #: Ensemble member to read from input
    pi_ensemble_member = 0

    def __init__(self, **kwargs):
        # Call parent class first for default behaviour.
        super().__init__(**kwargs)

        # Load rtcDataConfig.xml.  We assume this file does not change over the
        # life time of this object.
        self.__data_config = rtc.DataConfig(self._input_folder)

    def read(self):
        # Call parent class first for default behaviour.
        super().read()

        # rtcParameterConfig
        self.__parameter_config = []
        try:
            for pi_parameter_config_basename in self.pi_parameter_config_basenames:
                self.__parameter_config.append(
                    pi.ParameterConfig(self._input_folder, pi_parameter_config_basename)
                )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"PIMixin: {pi_parameter_config_basename}.xml not found in {self._input_folder}."
            )

        # Make a parameters dict for later access
        for parameter_config in self.__parameter_config:
            for location_id, model_id, parameter_id, value in parameter_config:
                try:
                    parameter = self.__data_config.parameter(parameter_id, location_id, model_id)
                except KeyError:
                    parameter = parameter_id
                self.io.set_parameter(parameter, value)

        try:
            self.__timeseries_import = pi.Timeseries(
                self.__data_config,
                self._input_folder,
                self.timeseries_import_basename,
                binary=self.pi_binary_timeseries,
                pi_validate_times=self.pi_validate_timeseries,
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"PIMixin: {self.timeseries_import_basename}.xml not found in {self._input_folder}"
            )

        self.__timeseries_export = pi.Timeseries(
            self.__data_config,
            self._output_folder,
            self.timeseries_export_basename,
            binary=self.pi_binary_timeseries,
            pi_validate_times=False,
            make_new_file=True,
        )

        # Convert timeseries timestamps to seconds since t0 for internal use
        timeseries_import_times = self.__timeseries_import.times

        # Timestamp check
        if self.pi_validate_timeseries:
            for i in range(len(timeseries_import_times) - 1):
                if timeseries_import_times[i] >= timeseries_import_times[i + 1]:
                    raise ValueError("PIMixin: Time stamps must be strictly increasing.")

        # Check if the timeseries are equidistant
        dt = timeseries_import_times[1] - timeseries_import_times[0]
        if self.pi_validate_timeseries:
            for i in range(len(timeseries_import_times) - 1):
                if timeseries_import_times[i + 1] - timeseries_import_times[i] != dt:
                    raise ValueError(
                        "PIMixin: Expecting equidistant timeseries, the time step towards "
                        f"{timeseries_import_times[i + 1]} is not the same as the time step(s) "
                        "before. Set unit to nonequidistant if this is intended."
                    )

        # Stick timeseries into an AliasDict
        self.io.reference_datetime = self.__timeseries_import.forecast_datetime

        debug = logger.getEffectiveLevel() == logging.DEBUG
        for variable, values in self.__timeseries_import.items(self.pi_ensemble_member):
            self.io.set_timeseries(variable, timeseries_import_times, values)
            if debug and variable in self.get_variables():
                logger.debug(f"PIMixin: Timeseries {variable} replaced another aliased timeseries.")

    def write(self):
        # Call parent class first for default behaviour.
        super().write()

        times = self._simulation_times
        if len(set(np.diff(times))) == 1:
            dt = timedelta(seconds=times[1] - times[0])
        else:
            dt = None

        # Start of write output
        # Write the time range for the export file.
        self.__timeseries_export.times = [
            self.io.reference_datetime + timedelta(seconds=s) for s in times
        ]

        # Write other time settings
        self.__timeseries_export.forecast_datetime = self.io.reference_datetime
        self.__timeseries_export.dt = dt
        self.__timeseries_export.timezone = self.__timeseries_import.timezone

        # Write the ensemble properties for the export file.
        self.__timeseries_export.ensemble_size = 1
        self.__timeseries_export.contains_ensemble = self.__timeseries_import.contains_ensemble

        # For all variables that are output variables the values are
        # extracted from the results.
        for variable in self._io_output_variables:
            values = np.array(self._io_output[variable])
            # Check if ID mapping is present
            try:
                self.__data_config.pi_variable_ids(variable)
            except KeyError:
                logger.debug(
                    f"PIMixin: variable {variable} has no mapping defined in rtcDataConfig "
                    "so cannot be added to the output file."
                )
                continue

            # Add series to output file
            self.__timeseries_export.set(
                variable, values, unit=self.__timeseries_import.get_unit(variable)
            )

        # Write output file to disk
        self.__timeseries_export.write()

    @property
    def timeseries_import(self):
        """
        :class:`pi.Timeseries` object containing the input data.
        """
        return self.__timeseries_import

    @property
    def timeseries_import_times(self):
        """
        List of time stamps for which input data is specified.

        The time stamps are in seconds since t0, and may be negative.
        """
        return self.io.times_sec

    @property
    def timeseries_export(self):
        """
        :class:`pi.Timeseries` object for holding the output data.
        """
        return self.__timeseries_export

    def set_timeseries(self, variable, values, output=True, check_consistency=True, unit=None):
        if check_consistency:
            if len(self.times()) != len(values):
                raise ValueError(
                    f"PIMixin: Trying to set/append values {variable} with a different "
                    "length than the forecast length. Please make sure the values cover "
                    f"forecastDate through endDate with timestep {self.__timeseries_import.dt}."
                )

        if unit is None:
            unit = self.__timeseries_import.get_unit(variable)

        if output:
            try:
                self.__data_config.pi_variable_ids(variable)
            except KeyError:
                logger.debug(
                    f"PIMixin: variable {variable} has no mapping defined in rtcDataConfig "
                    "so cannot be added to the output file."
                )
            else:
                self.__timeseries_export.set(variable, values, unit=unit)

        self.__timeseries_import.set(variable, values, unit=unit)
        self.io.set_timeseries(variable, self.io.datetimes, values)

    def get_timeseries(self, variable):
        _, values = self.io.get_timeseries(variable)
        return values

    def set_unit(self, variable: str, unit: str):
        """
        Set the unit of a time series.

        :param variable:        Time series ID.
        :param unit:            Unit.
        """
        assert hasattr(self, "_PIMixin__timeseries_import"), (
            "set_unit can only be called after read() in pre() has finished."
        )
        self.__timeseries_import.set_unit(variable, unit, 0)
        self.__timeseries_export.set_unit(variable, unit, 0)
