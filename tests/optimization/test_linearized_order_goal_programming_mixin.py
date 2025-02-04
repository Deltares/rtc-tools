from test_case import TestCase

from rtctools.optimization.goal_programming_mixin import Goal, StateGoal
from rtctools.optimization.linearized_order_goal_programming_mixin import (
    LinearizedOrderGoal,
    LinearizedOrderGoalProgrammingMixin,
)

from .test_goal_programming import Model


class RangeGoalX(Goal):
    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state("x")

    function_range = (-10.0, 10.0)
    priority = 1
    order = 1
    target_min = 1.0
    target_max = 2.0


class RangeGoalUOrder1(StateGoal):
    state = "u"
    order = 1
    target_min = 0.0
    target_max = 0.0
    priority = 2


class RangeGoalUOrder2(RangeGoalUOrder1):
    order = 2


class RangeGoalUOrder2PerTimestep(RangeGoalUOrder2):
    def __init__(self, optimization_problem, t):
        self._t = t
        super().__init__(optimization_problem)

    def function(self, optimization_problem, ensemble_member):
        return optimization_problem.state_at(self.state, self._t)


class RangeGoalUOrder2Linearize(LinearizedOrderGoal, RangeGoalUOrder2):
    linearize_order = True


class RangeGoalUOrder2NoLinearize(LinearizedOrderGoal, RangeGoalUOrder2):
    linearize_order = False


class ModelRangeUOrder1(Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._results = []

    def priority_completed(self, priority):
        super().priority_completed(priority)
        self._results.append(dict(self.extract_results()))

    def goals(self):
        return []

    def path_goals(self):
        return [RangeGoalX(), RangeGoalUOrder1(self)]


class ModelRangeUOrder2(ModelRangeUOrder1):
    def path_goals(self):
        return [RangeGoalX(), RangeGoalUOrder2(self)]


class ModelRangeUOrder2OverruleLinearize(LinearizedOrderGoalProgrammingMixin, ModelRangeUOrder1):
    def goal_programming_options(self):
        options = super().goal_programming_options()
        options["linearize_goal_order"] = False
        return options

    def path_goals(self):
        return [RangeGoalX(), RangeGoalUOrder2Linearize(self)]


class ModelLinearGoalOrder1(LinearizedOrderGoalProgrammingMixin, ModelRangeUOrder1):
    pass


class ModelLinearGoalOrder2(LinearizedOrderGoalProgrammingMixin, ModelRangeUOrder2):
    pass


class ModelLinearGoalOrder2PerTimestep(ModelLinearGoalOrder2):
    def goals(self):
        return [RangeGoalUOrder2PerTimestep(self, t) for t in self.times()]

    def path_goals(self):
        return [RangeGoalX()]


class ModelLinearGoalOrder2OverruleNoLinearize(ModelLinearGoalOrder2):
    def path_goals(self):
        return [RangeGoalX(), RangeGoalUOrder2NoLinearize(self)]


class TestLinearGoalOrder(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem1 = ModelRangeUOrder1()
        cls.problem1.optimize()
        cls.problem1_linear = ModelLinearGoalOrder1()
        cls.problem1_linear.optimize()

        cls.problem2 = ModelRangeUOrder2()
        cls.problem2.optimize()
        cls.problem2_linear = ModelLinearGoalOrder2()
        cls.problem2_linear.optimize()

        cls.problem2_linear_overrule = ModelRangeUOrder2OverruleLinearize()
        cls.problem2_linear_overrule.optimize()

        cls.problem2_nonlinear_overrule = ModelLinearGoalOrder2OverruleNoLinearize()
        cls.problem2_nonlinear_overrule.optimize()

        cls.problem2_linear_per_timestep = ModelLinearGoalOrder2PerTimestep()
        cls.problem2_linear_per_timestep.optimize()

    def test_order_1_linear_equal(self):
        self.assertEqual(self.problem1.objective_value, self.problem1_linear.objective_value)

    def test_order_1_2_different(self):
        o1 = self.problem1.objective_value
        o2 = self.problem2.objective_value

        self.assertGreater(abs(o1 - o2), 0.25 * abs(o2))

    def test_order_2_linear_similar(self):
        o2 = self.problem2.objective_value
        o2_lin = self.problem2_linear.objective_value

        # 0.1 is the default max error when fitting, although this is just an
        # approximation when using 'balanced' mode.
        self.assertLess(abs(o2 - o2_lin), 0.1 * abs(o2))
        self.assertNotEqual(o2, o2_lin)

    def test_order_2_nonlinear_overrule_equal(self):
        self.assertEqual(
            self.problem2.objective_value, self.problem2_nonlinear_overrule.objective_value
        )

    def test_order_2_linear_overrule_equal(self):
        self.assertEqual(
            self.problem2_linear.objective_value, self.problem2_linear_overrule.objective_value
        )

    def test_order_2_per_timestep_equal(self):
        # Sometimes an error in the last decimal, probably due to different
        # order of instructions.
        self.assertAlmostEqual(
            self.problem2_linear_per_timestep.objective_value,
            self.problem2_linear.objective_value,
            1e-8,
        )
