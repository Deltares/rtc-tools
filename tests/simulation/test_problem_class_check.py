from test_case import TestCase

from rtctools.optimization.csv_mixin import CSVMixin as OptimizationCSVMixin
from rtctools.optimization.io_mixin import IOMixin as OptimizationIOMixin
from rtctools.optimization.pi_mixin import PIMixin as OptimizationPIMixin
from rtctools.util import run_simulation_problem


class BadProblemClass1(OptimizationCSVMixin):
    pass


class BadProblemClass2(OptimizationIOMixin):
    pass


class BadProblemClass3(OptimizationPIMixin):
    pass


class TestProblemClassCheck(TestCase):
    """
    Class for testing if problem classes are checked correctly.
    """

    def test_problem_class_check(self):
        """
        Check if simulation problem classes are checked correctly.
        """
        self.assertRaises(ValueError, run_simulation_problem, BadProblemClass1)
        self.assertRaises(ValueError, run_simulation_problem, BadProblemClass2)
        self.assertRaises(ValueError, run_simulation_problem, BadProblemClass3)
