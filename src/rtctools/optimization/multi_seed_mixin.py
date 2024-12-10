from typing import Dict, Iterable, Optional

from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.optimization.timeseries import Timeseries


class MultiSeedMixin(OptimizationProblem):
    """
    Enables a workflow to solve an optimization problem by trying multiple seeds.
    """

    def __init__(self, **kwargs):
        self.__selected_seed = None
        super().__init__(**kwargs)

    def seeds(self) -> Iterable[Optional[Dict[str, Timeseries]]]:
        """Return a list or iterator of seeds.

        When the seed is None, the default seed will be used.
        This method should be implemented by the user.
        """
        return [None]

    def seed(self, ensemble_member):
        if self.__selected_seed is None:
            return super().seed(ensemble_member)
        return self.__selected_seed

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        if preprocessing:
            self.pre()
        for seed in self.seeds():
            self.__selected_seed = seed
            success = super().optimize(
                preprocessing=False,
                postprocessing=False,
                log_solver_failure_as_error=log_solver_failure_as_error,
            )
            if success:
                break
        if postprocessing:
            self.post()
        return success
