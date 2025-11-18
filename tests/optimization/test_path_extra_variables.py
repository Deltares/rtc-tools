import logging

import casadi as ca
import numpy as np

from rtctools.optimization.collocated_integrated_optimization_problem import (
    CollocatedIntegratedOptimizationProblem,
)
from rtctools.optimization.modelica_mixin import ModelicaMixin
from rtctools.optimization.timeseries import Timeseries

from ..test_case import TestCase
from .data_path import data_path

logger = logging.getLogger("rtctools")
logger.setLevel(logging.WARNING)


class Model(ModelicaMixin, CollocatedIntegratedOptimizationProblem):
    def __init__(self):
        super().__init__(
            input_folder=data_path(),
            output_folder=data_path(),
            model_name="ModelWithInitial",
            model_folder=data_path(),
        )

    def times(self, variable=None):
        # Collocation points
        return np.linspace(0.0, 1.0, 21)

    def parameters(self, ensemble_member):
        parameters = super().parameters(ensemble_member)
        parameters["u_max"] = 2.0
        return parameters

    def constant_inputs(self, ensemble_member):
        constant_inputs = super().constant_inputs(ensemble_member)
        constant_inputs["constant_input"] = Timeseries(
            np.hstack(([self.initial_time, self.times()])),
            np.hstack(([1.0], np.linspace(1.0, 0.0, 21))),
        )
        return constant_inputs

    def bounds(self):
        bounds = super().bounds()
        bounds["u"] = (-2.0, 2.0)
        return bounds

    def set_timeseries(self, timeseries_id, timeseries, ensemble_member, **kwargs):
        # Do nothing
        pass

    def compiler_options(self):
        compiler_options = super().compiler_options()
        compiler_options["cache"] = False
        compiler_options["library_folders"] = []
        return compiler_options

    def constraints(self, ensemble_member):
        return [
            (self.state_at("x", 0.5, ensemble_member=ensemble_member), 1.0, np.inf),
            (self.state_at("x", 0.7, ensemble_member=ensemble_member), -np.inf, 0.8),
            (self.integral("x", 0.1, 1.0, ensemble_member=ensemble_member), -np.inf, 1.0),
        ]

    def path_objective(self, ensemble_member):
        return self.state("u") ** 2


class ModelExtraVars(Model):
    def pre(self):
        super().pre()

        self._additional_vars = []

        for i in range(len(self.times())):
            sym = ca.MX.sym("u2_t{}".format(i))
            self._additional_vars.append(sym)

    def constraints(self, ensemble_member):
        constraints = super().constraints(ensemble_member).copy()

        for sym, t in zip(self._additional_vars, self.times(), strict=False):
            x_sym = self.extra_variable(sym.name(), ensemble_member)
            constraints.append((x_sym - self.state_at("u", t) ** 2, 0, np.inf))

        return constraints

    def path_objective(self, ensemble_member):
        return ca.MX(0)

    def objective(self, ensemble_member):
        return ca.sum1(
            ca.vertcat(
                *[self.extra_variable(x.name(), ensemble_member) for x in self._additional_vars]
            )
        )

    @property
    def extra_variables(self):
        return self._additional_vars

    def bounds(self):
        bounds = super().bounds()

        for s in self._additional_vars:
            bounds[s.name()] = (0.0, 4.0)

        return bounds

    def seed(self, ensemble_member):
        seed = super().seed(ensemble_member)

        for s in self._additional_vars:
            seed[s.name()] = 0.0

        return seed


class ModelPathVars(Model):
    def pre(self):
        super().pre()

        u1 = ca.MX.sym("u**1")
        u2 = ca.MX.sym("u**2")
        u3 = ca.MX.sym("u**3")

        self._additional_path_vars = [u1, u2, u3]

    @property
    def path_variables(self):
        return self._additional_path_vars

    def path_constraints(self, ensemble_member):
        constraints = super().path_constraints(ensemble_member)

        for x in self._additional_path_vars:
            p = int(x.name()[-1])
            constraints.append((self.state(x.name()) - self.state("u") ** p, 0.0, 0.0))

        return constraints


class ModelExtraVarsNominalUnity(ModelExtraVars):
    def pre(self):
        super().pre()
        self._additional_var_names = [v.name() for v in self._additional_vars]

    def variable_nominal(self, variable):
        if variable in self._additional_var_names:
            return 1.0
        else:
            return super().variable_nominal(variable)

    def transcribe(self):
        discrete, lbx, ubx, lbg, ubg, x0, nlp = super().transcribe()
        self._lbx = lbx
        self._ubx = ubx
        self._x0 = x0
        return discrete, lbx, ubx, lbg, ubg, x0, nlp


class ModelPathVarsNominalUnity(ModelPathVars):
    def pre(self):
        super().pre()
        self._additional_var_names = [v.name() for v in self._additional_path_vars]

    def variable_nominal(self, variable):
        if variable in self._additional_var_names:
            return 1.0
        else:
            return super().variable_nominal(variable)

    def transcribe(self):
        discrete, lbx, ubx, lbg, ubg, x0, nlp = super().transcribe()
        self._lbx = lbx
        self._ubx = ubx
        self._x0 = x0
        return discrete, lbx, ubx, lbg, ubg, x0, nlp


class ModelExtraVarsNominalTwo(ModelExtraVarsNominalUnity):
    def variable_nominal(self, variable):
        if variable in self._additional_var_names:
            return 2.0
        else:
            return super().variable_nominal(variable)


class ModelPathVarsNominalTwo(ModelPathVarsNominalUnity):
    def variable_nominal(self, variable):
        if variable in self._additional_var_names:
            return 2.0
        else:
            return super().variable_nominal(variable)


class TestNominalsPathExtraVariables(TestCase):
    def setUp(self):
        self.tolerance = 1e-6

    def test_extra_variables_explicit_nominal(self):
        self.problem1 = ModelExtraVars()
        self.problem2 = ModelExtraVarsNominalUnity()
        self.problem1.optimize()
        self.problem2.optimize()

        self.assertEqual(self.problem1.objective_value, self.problem2.objective_value)

    def test_path_variables_explicit_nominal(self):
        self.problem1 = ModelPathVars()
        self.problem2 = ModelPathVarsNominalUnity()
        self.problem1.optimize()
        self.problem2.optimize()

        self.assertEqual(self.problem1.objective_value, self.problem2.objective_value)

    def test_extra_variables_nominal_difference(self):
        self.problem1 = ModelExtraVarsNominalUnity()
        self.problem2 = ModelExtraVarsNominalTwo()
        self.problem1.optimize()
        self.problem2.optimize()

        # Public API way of figuring out where in the state vector the path variables are stored
        state_vector_indices = []

        for p in [self.problem1, self.problem2]:
            inds = list(range(p.solver_input.size1()))
            f = ca.Function(
                "tmp",
                [p.solver_input],
                [ca.vertcat(*[p.state_vector(v) for v in p._additional_var_names])],
            )

            state_vector_indices.append(np.array(f(inds), dtype=int).ravel().tolist())

        inds_p1, inds_p2 = state_vector_indices

        self.assertEqual(inds_p1, inds_p2)
        self.assertTrue(
            np.array_equal(self.problem1._lbx[inds_p1], 2.0 * self.problem2._lbx[inds_p2])
        )
        self.assertTrue(
            np.array_equal(self.problem1._ubx[inds_p1], 2.0 * self.problem2._ubx[inds_p2])
        )
        self.assertTrue(
            np.array_equal(self.problem1._x0[inds_p1], 2.0 * self.problem2._x0[inds_p2])
        )
        self.assertAlmostEqual(
            self.problem1.solver_output[inds_p1],
            2.0 * self.problem2.solver_output[inds_p2],
            self.tolerance,
        )
        self.assertAlmostEqual(
            self.problem1.objective_value, self.problem2.objective_value, self.tolerance
        )

        results_1 = self.problem1.extract_results()
        results_2 = self.problem2.extract_results()

        for v in self.problem1._additional_var_names:
            self.assertAlmostEqual(results_1[v], results_2[v], self.tolerance)

    def test_path_variables_nominal_difference(self):
        self.problem1 = ModelPathVarsNominalUnity()
        self.problem2 = ModelPathVarsNominalTwo()
        self.problem1.optimize()
        self.problem2.optimize()

        # Public API way of figuring out where in the state vector the path variables are stored
        state_vector_indices = []

        for p in [self.problem1, self.problem2]:
            inds = list(range(p.solver_input.size1()))
            f = ca.Function(
                "tmp",
                [p.solver_input],
                [ca.vertcat(*[p.state_vector(v) for v in p._additional_var_names])],
            )

            state_vector_indices.append(np.array(f(inds), dtype=int).ravel().tolist())

        inds_p1, inds_p2 = state_vector_indices

        self.assertEqual(inds_p1, inds_p2)
        self.assertTrue(
            np.array_equal(self.problem1._lbx[inds_p1], 2.0 * self.problem2._lbx[inds_p2])
        )
        self.assertTrue(
            np.array_equal(self.problem1._ubx[inds_p1], 2.0 * self.problem2._ubx[inds_p2])
        )
        self.assertTrue(
            np.array_equal(self.problem1._x0[inds_p1], 2.0 * self.problem2._x0[inds_p2])
        )
        self.assertAlmostEqual(
            self.problem1.solver_output[inds_p1],
            2.0 * self.problem2.solver_output[inds_p2],
            self.tolerance,
        )
        self.assertAlmostEqual(
            self.problem1.objective_value, self.problem2.objective_value, self.tolerance
        )

        results_1 = self.problem1.extract_results()
        results_2 = self.problem2.extract_results()

        for v in self.problem1._additional_var_names:
            self.assertAlmostEqual(results_1[v], results_2[v], self.tolerance)
