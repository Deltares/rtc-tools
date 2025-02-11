from typing import Iterable

from rtctools.optimization.optimization_problem import OptimizationProblem


class MultiRunMixin(OptimizationProblem):
    """
    Enables a workflow to solve an optimization problem with multiple attempts.
    """

    def __init__(self, **kwargs):
        self.__run_id = None
        super().__init__(**kwargs)

    def run_ids(self) -> Iterable:
        """Return a list or iterator of run identifiers.

        This method should be implemented by the user.
        """
        raise NotImplementedError("This method should be implemented by the user.")

    def run_id(self):
        """Return the selected run identifier."""
        return self.__run_id

    def optimize(
        self,
        preprocessing: bool = True,
        postprocessing: bool = True,
        log_solver_failure_as_error: bool = True,
    ) -> bool:
        if preprocessing:
            self.pre()
        for run_id in self.run_ids():
            self.__run_id = run_id
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
