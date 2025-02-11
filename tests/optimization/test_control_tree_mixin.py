import logging

import numpy as np
from test_case import TestCase

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.control_tree_mixin import ControlTreeMixin
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.DEBUG)


class Model(ControlTreeMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self, branching_times):
        super().__init__(model_name="ModelWithInitial", model_folder=data_path())
        self._branching_times = branching_times

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    def parameters(self, ensemble_member):
        parameters = super().parameters(ensemble_member)
        parameters["u_max"] = 2.0
        return parameters

    def pre(self):
        # Do nothing
        pass

    @property
    def ensemble_size(self):
        return 3

    def control_tree_options(self):
        return {
            "forecast_variables": ["constant_input"],
            "branching_times": self._branching_times,
            "k": 2,
        }

    def constant_inputs(self, ensemble_member):
        # Constant inputs
        if ensemble_member == 0:
            return {"constant_input": Timeseries(self.times(), np.linspace(1.0, 0.0, 21))}
        elif ensemble_member == 1:
            return {"constant_input": Timeseries(self.times(), np.linspace(0.99, 0.5, 21))}
        else:
            return {"constant_input": Timeseries(self.times(), np.linspace(0.98, 1.0, 21))}

    def bounds(self):
        # Variable bounds
        return {"u": (-2.0, 2.0)}

    def seed(self, ensemble_member):
        # No particular seeding
        return {}

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2

    def constraints(self, ensemble_member):
        # No additional constraints
        return []

    def post(self):
        # Do
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class TestControlTreeMixin1(TestCase):
    @property
    def branching_times(self):
        return [0.1, 0.2]

    def setUp(self):
        self.problem = Model(self.branching_times)
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_tree(self):
        v = [
            self.problem.control_vector("u", ensemble_member)
            for ensemble_member in range(self.problem.ensemble_size)
        ]
        for i, t in enumerate(self.problem.times()):
            if t < self.branching_times[0]:
                self.assertEqual(len({repr(_v[i]) for _v in v}), 1)
            elif t < self.branching_times[1]:
                self.assertEqual(len({repr(_v[i]) for _v in v}), 2)
            else:
                self.assertEqual(len({repr(_v[i]) for _v in v}), 3)


class TestControlTreeMixin2(TestControlTreeMixin1):
    @property
    def branching_times(self):
        return [0.0, 0.1, 0.2]


class TestControlTreeMixin3(TestControlTreeMixin1):
    @property
    def branching_times(self):
        return np.linspace(0.0, 1.0, 21)[:-1]


class TestControlTreeMixin4(TestControlTreeMixin1):
    @property
    def branching_times(self):
        return np.linspace(0.0, 1.0, 21)[1:-1]


class TestControlTreeMixin5(TestControlTreeMixin1):
    @property
    def branching_times(self):
        return np.linspace(0.0, 1.0, 21)[1:]


class ModelDijkverruiming(ControlTreeMixin, ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self):
        super().__init__(model_name="ModelWithInitial", model_folder=data_path())

    def times(self, variable=None):
        # Collocation points
        return np.array([0.0, 0.25, 0.5, 0.75])

    def parameters(self, ensemble_member):
        parameters = super().parameters(ensemble_member)
        parameters["u_max"] = 2.0
        return parameters

    def pre(self):
        # Do nothing
        pass

    @property
    def ensemble_size(self):
        return 12

    def control_tree_options(self):
        return {
            "forecast_variables": ["constant_input"],
            "branching_times": [0.25, 0.5, 0.75],
            "k": 3,
        }

    def constant_inputs(self, ensemble_member):
        # Constant inputs
        if ensemble_member == 0:
            v = [16, 16, 16, 16]
        elif ensemble_member == 1:
            v = [16, 16, 16, 17]
        elif ensemble_member == 2:
            v = [16, 16, 17, 16]
        elif ensemble_member == 3:
            v = [16, 16, 17, 17]
        elif ensemble_member == 4:
            v = [16, 16, 17, 18]
        elif ensemble_member == 5:
            v = [16, 17, 16, 16]
        elif ensemble_member == 6:
            v = [16, 17, 16, 17]
        elif ensemble_member == 7:
            v = [16, 17, 17, 16]
        elif ensemble_member == 8:
            v = [16, 17, 17, 17]
        elif ensemble_member == 9:
            v = [16, 17, 17, 18]
        elif ensemble_member == 10:
            v = [16, 17, 18, 17]
        elif ensemble_member == 11:
            v = [16, 17, 18, 18]
        return {"constant_input": Timeseries(self.times(), np.array(v))}

    def bounds(self):
        # Variable bounds
        return {"u": (-2.0, 2.0)}

    def seed(self, ensemble_member):
        # No particular seeding
        return {}

    def objective(self, ensemble_member):
        # Quadratic penalty on state 'x' at final time
        xf = self.state_at("x", self.times("x")[-1], ensemble_member=ensemble_member)
        return xf**2

    def constraints(self, ensemble_member):
        # No additional constraints
        return []

    def post(self):
        # Do
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options


class TestDijkverruiming(TestCase):
    def setUp(self):
        self.problem = ModelDijkverruiming()
        self.problem.optimize()
        self.tolerance = 1e-6

    def test_tree(self):
        v = [
            self.problem.control_vector("u", ensemble_member)
            for ensemble_member in range(self.problem.ensemble_size)
        ]

        # t = 0
        for ensemble_member in range(0, self.problem.ensemble_size):
            self.assertTrue(repr(v[0][0]) == repr(v[ensemble_member][0]))

        # t = 0.25
        for ensemble_member in range(0, 5):
            self.assertTrue(repr(v[0][1]) == repr(v[ensemble_member][1]))
        self.assertTrue(repr(v[0][1]) != repr(v[5][1]))
        for ensemble_member in range(5, 12):
            self.assertTrue(repr(v[5][1]) == repr(v[ensemble_member][1]))

        # t = 0.5
        for ensemble_member in range(0, 2):
            self.assertTrue(repr(v[0][2]) == repr(v[ensemble_member][2]))
        self.assertTrue(repr(v[0][2]) != repr(v[2][2]))
        for ensemble_member in range(2, 5):
            self.assertTrue(repr(v[2][2]) == repr(v[ensemble_member][2]))
        self.assertTrue(repr(v[0][2]) != repr(v[5][2]))
        self.assertTrue(repr(v[2][2]) != repr(v[5][2]))
        for ensemble_member in range(5, 7):
            self.assertTrue(repr(v[5][2]) == repr(v[ensemble_member][2]))
        self.assertTrue(repr(v[0][2]) != repr(v[7][2]))
        self.assertTrue(repr(v[2][2]) != repr(v[7][2]))
        self.assertTrue(repr(v[5][2]) != repr(v[7][2]))
        for ensemble_member in range(7, 10):
            self.assertTrue(repr(v[7][2]) == repr(v[ensemble_member][2]))

        # t = 0.75
        for ensemble_member_1 in range(self.problem.ensemble_size):
            for ensemble_member_2 in range(ensemble_member_1):
                self.assertTrue(repr(v[ensemble_member_1][3]) != repr(v[ensemble_member_2][3]))
