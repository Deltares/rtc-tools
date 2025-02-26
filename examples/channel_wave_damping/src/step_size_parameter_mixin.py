import numpy as np

from rtctools.optimization.optimization_problem import OptimizationProblem


class StepSizeParameterMixin(OptimizationProblem):
    step_size = 5 * 60  # 5 minutes

    def times(self, variable=None):
        times = super().times(variable)
        return np.arange(times[0], times[-1], self.step_size)

    def parameters(self, ensemble_member):
        p = super().parameters(ensemble_member)
        p["step_size"] = self.step_size
        return p
