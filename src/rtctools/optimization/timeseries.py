import casadi as ca
import numpy as np


class Timeseries:
    """
    Time series object, bundling time stamps with values.
    """

    def __init__(self, times: np.ndarray, values: float | np.ndarray | list | ca.DM):
        """
        Create a new time series object.

        :param times:  Iterable of time stamps.
        :param values: Iterable of values.
        """
        self.__times = times

        if isinstance(values, ca.DM):
            # Note that a ca.DM object has no __iter__ attribute, which we
            # want it to have. We also want it to store it as a _flat_ array,
            # not a 2-D column vector.
            assert values.shape[0] == 1 or values.shape[1] == 1, "Only 1D ca.DM objects supported"
            values = values.toarray().ravel()
        elif isinstance(values, (np.ndarray, list)) and len(values) == 1:
            values = values[0]

        if hasattr(values, "__iter__"):
            self.__values = np.array(values, dtype=np.float64, copy=True)
        else:
            self.__values = np.full_like(times, values, dtype=np.float64)

    @property
    def times(self) -> np.ndarray:
        """
        Array of time stamps.
        """
        return self.__times

    @property
    def values(self) -> np.ndarray:
        """
        Array of values.
        """
        return self.__values

    def __neg__(self) -> "Timeseries":
        return self.__class__(self.times, -self.values)

    def __repr__(self) -> str:
        return f"Timeseries({self.__times}, {self.__values})"

    def __eq__(self, other: "Timeseries") -> bool:
        return np.array_equal(self.times, other.times) and np.array_equal(self.values, other.values)
