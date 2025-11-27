import logging
from collections import OrderedDict

import rtctools.data.netcdf as netcdf
from rtctools.optimization.io_mixin import IOMixin

logger = logging.getLogger("rtctools")


class NetCDFMixin(IOMixin):
    """
    Adds NetCDF I/O to your optimization problem.

    During preprocessing, a file named timeseries_import.nc is read from the ``input`` subfolder.
    During postprocessing a file named timeseries_export.nc is written to the ``output`` subfolder.

    Both the input and output nc files are expected to follow the FEWS format for
    scalar data in a NetCDF file, i.e.:

    - They must contain a variable with the station ids (location ids) which can
      be recognized by the attribute `cf_role` set to `timeseries_id`.
    - They must contain a time variable with attributes `standard_name` = `time`
      and `axis` = `T`

    From the input file, all 2-D (or 3-D in case of ensembles) variables with dimensions equal
    to the station ids and time variable (and realization) are read.

    To map the NetCDF parameter identifier to and from an RTC-Tools variable name,
    the overridable methods :py:meth:`netcdf_id_to_variable` and
    :py:meth:`netcdf_id_from_variable` are used.

    :cvar netcdf_validate_timeseries:
        Check consistency of timeseries. Default is ``True``
    """

    #: Check consistency of timeseries.
    netcdf_validate_timeseries = True

    def netcdf_id_to_variable(self, station_id: str, parameter: str) -> str:
        """
        Maps the station_id and the parameter name to the variable name to be
        used in RTC-Tools.

        :return: The variable name used in RTC-Tools
        """
        return f"{station_id}__{parameter}"

    def netcdf_id_from_variable(self, variable_name: str) -> tuple[str, str]:
        """
        Maps the variable name in RTC-Tools to a station_id and parameter name
        for writing to a NetCDF file.

        :return: A pair of station_id and parameter
        """
        return variable_name.split("__")

    def read(self):
        # Call parent class first for default behaviour
        super().read()

        dataset = netcdf.ImportDataset(self._input_folder, self.timeseries_import_basename)
        # Although they are not used outside of this method, we add some
        # variables to self for debugging purposes
        self.__timeseries_import = dataset

        # store the import times
        times = self.__timeseries_times = dataset.read_import_times()
        self.io.reference_datetime = self.__timeseries_times[0]

        # Timestamp check
        self.__dt = times[1] - times[0] if len(times) >= 2 else 0
        for i in range(len(times) - 1):
            if times[i + 1] - times[i] != self.__dt:
                self.__dt = None
                break

        if self.netcdf_validate_timeseries:
            # check if strictly increasing
            for i in range(len(times) - 1):
                if times[i] >= times[i + 1]:
                    raise Exception("NetCDFMixin: Time stamps must be strictly increasing.")

        # store the station data for later use
        self.__stations = dataset.read_station_data()
        # read all available timeseries from the dataset
        timeseries_var_keys = dataset.find_timeseries_variables()

        for parameter in timeseries_var_keys:
            for i, station_id in enumerate(self.__stations.station_ids):
                name = self.netcdf_id_to_variable(station_id, parameter)

                if dataset.ensemble_member_variable is not None:
                    if dataset.ensemble_member_variable.dimensions[
                        0
                    ] in dataset.variable_dimensions(parameter):
                        for ensemble_member_index in range(self.__timeseries_import.ensemble_size):
                            values = dataset.read_timeseries_values(
                                i, parameter, ensemble_member_index
                            )
                            self.io.set_timeseries(
                                name, self.__timeseries_times, values, ensemble_member_index
                            )
                    else:
                        values = dataset.read_timeseries_values(i, parameter, 0)
                        for ensemble_member_index in range(self.__timeseries_import.ensemble_size):
                            self.io.set_timeseries(
                                name, self.__timeseries_times, values, ensemble_member_index
                            )
                else:
                    values = dataset.read_timeseries_values(i, parameter, 0)
                    self.io.set_timeseries(name, self.__timeseries_times, values, 0)

                logger.debug(
                    f'Read timeseries data for station id "{station_id}" and '
                    f'parameter "{parameter}", stored under variable name "{name}"'
                )

        logger.debug("NetCDFMixin: Read timeseries")

    def write(self):
        # Call parent class first for default behaviour
        super().write()

        dataset = netcdf.ExportDataset(self._output_folder, self.timeseries_export_basename)

        times = [(dt - self.__timeseries_times[0]).seconds for dt in self.__timeseries_times]
        dataset.write_times(times, self.initial_time, self.io.reference_datetime)

        output_variables = [sym.name() for sym in self.output_variables]

        output_station_ids, output_parameter_ids = zip(
            *(self.netcdf_id_from_variable(var_name) for var_name in output_variables), strict=True
        )

        # Make sure that output_station_ids and output_parameter_ids are
        # unique, but make sure to avoid non-deterministic ordering.
        unique_station_ids = list(OrderedDict.fromkeys(output_station_ids))
        unique_parameter_ids = list(OrderedDict.fromkeys(output_parameter_ids))

        dataset.write_station_data(self.__stations, unique_station_ids)
        dataset.write_ensemble_data(self.ensemble_size)

        dataset.create_variables(unique_parameter_ids, self.ensemble_size)

        for ensemble_member in range(self.ensemble_size):
            results = self.extract_results(ensemble_member)

            for var_name, station_id, parameter_id in zip(
                output_variables, output_station_ids, output_parameter_ids, strict=True
            ):
                # determine the output values
                try:
                    values = results[var_name]
                    if len(values) != len(times):
                        values = self.interpolate(
                            times, self.times(var_name), values, self.interpolation_method(var_name)
                        )
                except KeyError:
                    try:
                        ts = self.get_timeseries(var_name, ensemble_member)
                        if len(ts.times) != len(times):
                            values = self.interpolate(times, ts.times, ts.values)
                        else:
                            values = ts.values
                    except KeyError:
                        logger.error(
                            f"NetCDFMixin: Output requested for non-existent variable {var_name}. "
                            "Will not be in output file."
                        )
                        continue

                dataset.write_output_values(
                    station_id, parameter_id, ensemble_member, values, self.ensemble_size
                )

        dataset.close()
