from typing import Any, Dict, Iterable

from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.optimization.timeseries import Timeseries


class MultiSeedMixin(OptimizationProblem):
    """
    Enables a workflow to solve an optimization problem by trying multiple seeds.
    """

    def __init__(self, **kwargs):
        self.__selected_seed_id = None
        super().__init__(**kwargs)

    def use_seed_id(self) -> bool:
        """Return ``True`` if the selected seed id is used.

        Return ``True`` if the seed corresponding to the selected seed identifier is used
        for the current run.
        By default, this is ``True``.
        Overwrite this method when in some cases the seed is not based on the seed id,
        e.g. in case of goal programming, return False after the first priority,
        or in case of homotopy, return ``False`` after the homotopy parameter is increased.
        """
        return True

    def selected_seed_id(self) -> Any:
        """Get the selected seed identifier.

        If the selected seed id is None, use the default seed.
        """
        return self.__selected_seed_id

    def seed_ids(self) -> Iterable:
        """Return a list or iterator of seed identifiers.

        When the id is None, the default seed will be used.
        This method should be implemented by the user.
        """
        raise NotImplementedError("This method should be implemented by the user.")

    def seed_from_id(self, seed_id) -> Dict[str, Timeseries]:
        """
        Get the seed timeseries from the selected identifier.

        This method should be implemented by the user.
        """
        del seed_id
        raise NotImplementedError("This method should be implemented by the user.")

    def seed(self, ensemble_member):
        if self.selected_seed_id() is None or not self.use_seed_id():
            return super().seed(ensemble_member)
        seed: dict = super().seed(ensemble_member).copy()  # Copy to prevent updating cached seeds.
        seed_from_id = self.seed_from_id(self.selected_seed_id())
        seed.update(seed_from_id)
        return seed

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        if preprocessing:
            self.pre()
        for seed_id in self.seed_ids():
            self.__selected_seed_id = seed_id
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
