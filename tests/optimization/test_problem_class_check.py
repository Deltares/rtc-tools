from rtctools.simulation.csv_mixin import CSVMixin as SimulationCSVMixin
from rtctools.simulation.io_mixin import IOMixin as SimulationIOMixin
from rtctools.simulation.pi_mixin import PIMixin as SimulationPIMixin
from rtctools.util import run_optimization_problem

from ..test_case import TestCase


class BadProblemClass1(SimulationCSVMixin):
    pass


class BadProblemClass2(SimulationIOMixin):
    pass


class BadProblemClass3(SimulationPIMixin):
    pass


class TestProblemClassCheck(TestCase):
    """
    Class for testing if problem classes are checked correctly.
    """

    def test_problem_class_check(self):
        """
        Check if optimization problem classes are checked correctly.
        """
        self.assertRaises(ValueError, run_optimization_problem, BadProblemClass1)
        self.assertRaises(ValueError, run_optimization_problem, BadProblemClass2)
        self.assertRaises(ValueError, run_optimization_problem, BadProblemClass3)
