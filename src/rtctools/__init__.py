"""
RTC-Tools: Deltares toolbox for control and optimization of environmental systems.

IMPORTANT: This __init__.py has an intentional import side effect:
    It checks the RTCTOOLS_PRELOAD_SOLVER_LIBS environment variable and
    preloads custom solver libraries if specified.

Why this side effect exists:
    - Custom solver libraries MUST be loaded before CasADi is imported
    - CasADi is a C extension that cannot be reloaded once imported
    - This is the only reliable place to intercept imports before CasADi loads
    - The side effect is opt-in: only occurs if environment variable is set

If RTCTOOLS_PRELOAD_SOLVER_LIBS is not set, this is a no-op.

For more information, see: doc/advanced/custom_solver_versions.rst
"""

# Preload custom solver libraries if specified in environment
# This MUST happen before importing any optimization modules that depend on CasADi
from rtctools.solver_utils import _preload_solvers_from_environment
from rtctools.version import __version__

_preload_solvers_from_environment()

__all__ = ["__version__"]
