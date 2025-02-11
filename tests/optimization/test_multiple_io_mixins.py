import os
from itertools import permutations
from unittest import TestCase

import casadi as ca
import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.csv_mixin import CSVMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.netcdf_mixin import NetCDFMixin
from rtctools.optimization.pi_mixin import PIMixin

from .data_path import data_path


def get_model(mixins, test_folder):
    basefolder = os.path.join(data_path(), "multiple_io_mixins")
    folders = {
        "model": basefolder,
        "different_ensemble_sizes": os.path.join(basefolder, "different_ensemble_sizes"),
        "different_initial_date": os.path.join(basefolder, "different_initial_date"),
        "different_timestep": os.path.join(basefolder, "different_timestep"),
        "different_values": os.path.join(basefolder, "different_values"),
    }

    class Model(*mixins, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
        def __init__(self, **kwargs):
            kwargs["model_name"] = "Model"
            kwargs["input_folder"] = folders[test_folder]
            kwargs["output_folder"] = folders[test_folder]
            kwargs["model_folder"] = folders["model"]
            super().__init__(**kwargs)

        csv_ensemble_mode = True

        def objective(self, ensemble_member):
            return ca.MX(1)

        def compiler_options(self):
            compiler_options = super().compiler_options()
            compiler_options["cache"] = False
            compiler_options["library_folders"] = []
            return compiler_options

    return Model()


class TestMultipleIOMixins(TestCase):
    mixins = [CSVMixin, PIMixin, NetCDFMixin]

    def test_differences_in_values(self):
        """
        Values read in by one mixin are overwritten by values attained from
        a mixin to its left among the superclasses.
        """

        expected_outputs = {
            CSVMixin: {0: [1, 1, 1, 1, 3], 1: [1, 1, 1, 3, 4]},
            PIMixin: {0: [1, 0, 1, 1, 5], 1: [1, 2, 1, 1, 5]},
            NetCDFMixin: {0: [1] * 5, 1: [2] * 5},
        }

        for permutlen in (2, 3):
            for permut in permutations(self.mixins, permutlen):
                problem = get_model(permut, "different_values")
                problem.optimize()
                self.assertEqual(problem.ensemble_size, 2)

                # Expected output is that of the left-most mixin
                expected_output = expected_outputs[permut[0]]

                for ensemble_member in range(problem.ensemble_size):
                    output = problem.extract_results(ensemble_member)["loc_a__x"]
                    np.testing.assert_array_equal(
                        output,
                        expected_output[ensemble_member],
                        "class permutation = {}, ensemble member = {}".format(
                            [x.__name__ for x in permut], ensemble_member
                        ),
                    )

    def test_differences_in_parameters(self):
        """
        Parameters read in by one mixin are overwritten by parameters attained
        from a mixin to its left among the superclasses. NetCDF does not
        support loading parameters from files and is not included in the
        tests.
        """
        subset_mixins = [CSVMixin, PIMixin]
        expected_outputs = {CSVMixin: (2.0, 3.0), PIMixin: (1.0, 1.0)}

        for permut in permutations(subset_mixins, 2):
            problem = get_model(permut, "different_values")
            problem.optimize()
            self.assertEqual(problem.ensemble_size, 2)

            expected_output = expected_outputs[permut[0]]

            for ensemble_member in range(problem.ensemble_size):
                output = problem.parameters(ensemble_member)["k"]
                self.assertEqual(
                    output,
                    expected_output[ensemble_member],
                    "class permutation = {}, ensemble member = {}".format(
                        [x.__name__ for x in permut], ensemble_member
                    ),
                )

    def test_differences_in_ensemble_sizes(self):
        """
        Values associated to an ensemble member and attained by use of a mixin are overwritten
        by values attained from mixin to its left among the superclasses if this ensemble
        member is present in the data read by this mixin.
        """

        outputs = {
            CSVMixin: {
                0: [1, 8, 1, 1, 3],
                1: [1, 1, 7, 3, 4],
                2: [1, 5, 7, 3, 4],
                3: [1, 9, 7, 3, 4],
            },
            PIMixin: {0: [9, 0, 0, 1, 5]},
            NetCDFMixin: {0: [1] * 5, 1: [2] * 5},
        }

        for permutlen in (2, 3):
            for permut in permutations(self.mixins, permutlen):
                problem = get_model(permut, "different_ensemble_sizes")
                problem.optimize()

                expected_size = max(len(outputs[x]) for x in permut)
                self.assertEqual(
                    problem.ensemble_size,
                    expected_size,
                    "class permutation = {}".format([x.__name__ for x in permut]),
                )

                # Construct reference output for this permutation
                expected_output = [None] * expected_size
                for ensemble_member in range(expected_size):
                    for mixin in reversed(permut):
                        try:
                            expected_output[ensemble_member] = outputs[mixin][ensemble_member]
                        except KeyError:
                            pass

                # Compare output to reference
                for ensemble_member in range(expected_size):
                    output = problem.extract_results(ensemble_member)["loc_a__x"]
                    np.testing.assert_array_equal(
                        output,
                        expected_output[ensemble_member],
                        "class permutation = {}, ensemble member = {}".format(
                            [x.__name__ for x in permut], ensemble_member
                        ),
                    )

    def test_differences_in_initial_dates(self):
        """
        Differences in initial dates between files read by the mixins will
        result in runtime errors.
        """
        for permutlen in (2, 3):
            for permut in permutations(self.mixins, permutlen):
                problem = get_model(permut, "different_initial_date")
                with self.assertRaisesRegex(RuntimeError, "ensure all .* the same datetimes"):
                    problem.optimize()

    def test_differences_in_timesteps(self):
        """
        Differences in timesteps between files read by the mixins will result
        in runtime errors.
        """
        for permutlen in (2, 3):
            for permut in permutations(self.mixins, permutlen):
                problem = get_model(permut, "different_timestep")
                with self.assertRaisesRegex(RuntimeError, "ensure all .* the same datetimes"):
                    problem.optimize()
