from .goal_programming_mixin import Goal, GoalProgrammingMixin


class _MeasurementGoal(Goal):
    def __init__(self, state, measurement_id, max_deviation=1.0):
        self.__state = state
        self.__measurement_id = measurement_id

        self.function_nominal = max_deviation

    def function(self, optimization_problem, ensemble_member):
        op = optimization_problem
        return op.state_at(self.__state, op.initial_time, ensemble_member) - op.timeseries_at(
            self.__measurement_id, op.initial_time, ensemble_member
        )

    order = 2
    priority = -2


class _SmoothingGoal(Goal):
    def __init__(self, state1, state2, max_deviation=1.0):
        self.__state1 = state1
        self.__state2 = state2

        self.function_nominal = max_deviation

    def function(self, optimization_problem, ensemble_member):
        op = optimization_problem
        return op.state_at(self.__state1, op.initial_time, ensemble_member) - op.state_at(
            self.__state2, op.initial_time, ensemble_member
        )

    order = 2
    priority = -1


class InitialStateEstimationMixin(GoalProgrammingMixin):
    """
    Adds initial state estimation to your optimization problem *using goal programming*.

    Before any other goals are evaluated, first, the deviation between initial
    state measurements and their respective model states is minimized in the
    least squares sense (1DVAR, priority -2). Secondly, the distance between
    pairs of states is minimized, again in the least squares sense, so that
    "smooth" initial guesses are provided for states without measurements
    (priority -1).

    .. note::

        There are types of problems where, in addition to minimizing
        differences between states and measurements, it is advisable to
        perform a steady-state initialization using additional initial-time
        model equations.  For hydraulic models, for instance, it is often
        helpful to require that the time-derivative of the flow variables
        vanishes at the initial time.

    """

    def initial_state_measurements(self) -> list[tuple[str, str] | tuple[str, str, float]]:
        """
        List of pairs ``(state, measurement_id)`` or triples ``(state, measurement_id,
        max_deviation)``, relating states to measurement time series IDs.

        The default maximum deviation is ``1.0``.
        """
        return []

    def initial_state_smoothing_pairs(self) -> list[tuple[str, str] | tuple[str, str, float]]:
        """
        List of pairs ``(state1, state2)`` or triples ``(state1, state2, max_deviation)``, relating
        states the distance of which is to be minimized.

        The default maximum deviation is ``1.0``.
        """
        return []

    def goals(self):
        g = super().goals()

        for measurement in self.initial_state_measurements():
            g.append(_MeasurementGoal(*measurement))

        for smoothing_pair in self.initial_state_smoothing_pairs():
            g.append(_SmoothingGoal(*smoothing_pair))

        return g
