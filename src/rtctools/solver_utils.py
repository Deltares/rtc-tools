"""
Utilities for preloading custom solver libraries with CasADi.

This module provides functionality to use custom versions of solver libraries
(HiGHS, IPOPT, BONMIN, etc.) instead of those bundled with CasADi.

Architecture:
    This module uses module-level state (_preloaded_solvers dict) to track which
    solver libraries have been preloaded. This is necessary because:

    1. Library preloading must happen BEFORE CasADi imports
    2. CasADi is a C extension that cannot be reloaded
    3. The preloading decision is process-wide and permanent

    The module-level state is protected by threading.Lock for concurrent access.

Thread Safety:
    This module uses a threading.Lock to protect access to the _preloaded_solvers
    dictionary. All public functions are thread-safe for concurrent calls.

    The expensive ctypes.CDLL() operation happens OUTSIDE the lock to allow
    concurrent library loading by different threads. A double-check pattern is
    used after loading to handle the race condition where multiple threads try
    to load the same library simultaneously.

Import Side Effects:
    When rtctools is imported, this module's _preload_solvers_from_environment()
    function is automatically called from rtctools.__init__.py. This is an
    intentional design decision to ensure custom solvers are loaded before CasADi.

    The side effect is opt-in: it only occurs if RTCTOOLS_PRELOAD_SOLVER_LIBS
    environment variable is set. If not set, the import is a no-op.

Testing Considerations:
    - Module state persists across test runs in the same process
    - Tests should clean up _preloaded_solvers in setUp/tearDown
    - Integration tests require fresh Python processes
    - See tests/optimization/test_solver_preload.py for examples
"""

import ctypes
import logging
import os
import sys
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

# Thread-safe lock for solver preloading operations
_preload_lock = Lock()

# Track preloaded solvers to avoid duplicates and enforce priority
# Note: Access to this dict should be protected by _preload_lock in multi-threaded contexts
_preloaded_solvers: dict[str, Path] = {}

# Track if preloading was requested but failed due to import order
_preload_failed_due_to_import_order: bool = False


def preload_custom_solver_library(library_path: str | Path, solver_name: str | None = None) -> bool:
    """
    Preload a custom solver library before CasADi imports it.

    This function allows using custom versions of solver libraries instead of
    those bundled with CasADi. It must be called BEFORE importing casadi or
    any rtctools modules that depend on CasADi.

    Currently supported and tested solver: HiGHS.
    Note: IPOPT preloading does not work with precompiled binaries on Windows - public
    binaries use incompatible compilers (Intel vs CasADi's GCC/MinGW), and Julia
    GCC-compiled binaries have missing dependencies. Workaround: use preloading in a
    Linux environment (e.g., Docker, WSL2) with conda-forge GCC-compiled IPOPT binaries.

    Args:
        library_path: Path to the custom solver library file
                     (e.g., libhighs.dll, libipopt.so, etc.)
        solver_name: Optional solver name for logging purposes (e.g., "HiGHS", "IPOPT")

    Returns:
        True if library was successfully preloaded or already preloaded from same path.
        False if already preloaded from a different path (first path takes precedence).

    Raises:
        FileNotFoundError: If library_path does not exist
        RuntimeError: If library fails to load

    Example:
        >>> from rtctools.solver_utils import preload_custom_solver_library
        >>> # Must be called before any CasADi imports
        >>> preload_custom_solver_library('/opt/highs-1.12/lib/libhighs.so', 'HiGHS')
        >>> # Now import optimization modules
        >>> from rtctools.optimization.optimization_problem import OptimizationProblem

    Environment Variable:
        Alternatively, set RTCTOOLS_PRELOAD_SOLVER_LIBS environment variable:

        Linux/macOS:
            export RTCTOOLS_PRELOAD_SOLVER_LIBS="highs:/opt/highs/lib/libhighs.so"

        Windows:
            set RTCTOOLS_PRELOAD_SOLVER_LIBS=highs:C:/highs/bin/libhighs.dll

        Multiple solvers:
            export RTCTOOLS_PRELOAD_SOLVER_LIBS="highs:/path/libhighs.so,ipopt:/path/libipopt.so"
    """
    library_path = Path(library_path).resolve()

    if not library_path.exists():
        raise FileNotFoundError(f"Solver library not found: {library_path}")

    if solver_name is None:
        stem = library_path.stem
        solver_name = stem[3:] if stem.lower().startswith("lib") else stem

    # Check if already preloaded (with minimal lock time)
    with _preload_lock:
        if solver_name in _preloaded_solvers:
            stored_path = _preloaded_solvers[solver_name]
            try:
                same_location = stored_path.samefile(library_path)
            except FileNotFoundError:
                # Fall back to direct comparison if filesystem lookup fails
                same_location = stored_path == library_path

            if same_location:
                logger.debug(f"{solver_name} already preloaded from: {library_path}")
                return True
            else:
                logger.warning(
                    f"{solver_name} already preloaded from {_preloaded_solvers[solver_name]}, "
                    f"ignoring request to load from {library_path}"
                )
                return False

    # Load library OUTSIDE the lock to avoid blocking other threads
    try:
        logger.info(f"Preloading custom {solver_name} library from: {library_path}")

        if sys.platform.startswith("win"):
            # Windows: use winmode=0 for proper DLL loading
            ctypes.CDLL(str(library_path), winmode=0)
        else:
            # Linux/macOS: use RTLD_GLOBAL to make symbols available
            ctypes.CDLL(str(library_path), mode=ctypes.RTLD_GLOBAL)

        # Register the loaded library (acquire lock only for dict update)
        with _preload_lock:
            # Double-check: another thread might have loaded it while we were loading
            if solver_name in _preloaded_solvers:
                logger.debug(f"{solver_name} was loaded by another thread, using that")
                return True
            _preloaded_solvers[solver_name] = library_path.resolve()

        logger.info(f"Successfully preloaded {solver_name} library")
        return True

    except OSError as e:
        raise RuntimeError(
            f"Failed to preload {solver_name} library from {library_path}: {e}\n"
            f"Common causes:\n"
            f"  - Missing dependencies (check with ldd/otool/Dependencies.exe)\n"
            f"  - ABI incompatibility (different compiler or bitness)\n"
            f"  - Incorrect file path"
        ) from e


def _preload_solvers_from_environment() -> None:
    """
    Automatically preload solver libraries specified in environment variable.

    This is called automatically when rtctools is imported.

    Format:
        RTCTOOLS_PRELOAD_SOLVER_LIBS="solver_name:path,solver_name:path,..."

    Note:
        This uses ctypes to preload libraries, NOT the OS's library search path.
        Explicitly preloaded solvers (via preload_custom_solver_library) take
        precedence over environment variable specifications.

    Important:
        This only works if called BEFORE casadi is imported. If CasADi is already
        loaded, a warning will be logged and preloading will be skipped.
    """
    global _preload_failed_due_to_import_order

    env_var = os.environ.get("RTCTOOLS_PRELOAD_SOLVER_LIBS", "").strip()

    # Check if CasADi is already imported when preloading is requested
    if env_var and "casadi" in sys.modules:
        _preload_failed_due_to_import_order = True
        logger.warning(
            "CasADi is already imported. Custom solver preloading via "
            "RTCTOOLS_PRELOAD_SOLVER_LIBS will have no effect. "
            "To use custom solver libraries, either:\n"
            "  1. Set RTCTOOLS_PRELOAD_SOLVER_LIBS before importing any modules, OR\n"
            "  2. Use preload_custom_solver_library() explicitly before importing CasADi"
        )
        return

    if not env_var:
        return

    logger.debug("Processing RTCTOOLS_PRELOAD_SOLVER_LIBS environment variable")

    # Parse format: "highs:/path/to/libhighs.so,ipopt:/path/to/libipopt.so"
    for entry in env_var.split(","):
        entry = entry.strip()
        if not entry:
            continue

        if ":" not in entry:
            logger.warning(f"Invalid solver preload entry (expected 'name:path'): {entry}")
            continue

        solver_name, library_path = entry.split(":", 1)
        solver_name = solver_name.strip()
        library_path = library_path.strip()

        # Skip if already explicitly preloaded (thread-safe check)
        with _preload_lock:
            if solver_name in _preloaded_solvers:
                logger.debug(
                    f"{solver_name} already preloaded explicitly, "
                    f"skipping environment variable entry"
                )
                continue

        try:
            preload_custom_solver_library(library_path, solver_name)
        except Exception as e:
            # Log error but don't fail - allow graceful degradation
            logger.error(f"Failed to preload {solver_name} from environment: {e}")


def check_preload_import_order() -> None:
    """
    Check if custom solver preloading was requested but failed due to import order.

    This function can be called by user code to enforce strict checking of import order
    when custom solver preloading is critical. By default, RTC-Tools only logs a warning
    when import order prevents preloading.

    Raises:
        RuntimeError: If RTCTOOLS_PRELOAD_SOLVER_LIBS was set but CasADi was already
                     imported when rtctools attempted preloading (import order violation)

    Example:
        >>> import os
        >>> os.environ['RTCTOOLS_PRELOAD_SOLVER_LIBS'] = 'highs:/custom/libhighs.so'
        >>> from rtctools.solver_utils import check_preload_import_order
        >>> check_preload_import_order()  # Raises if import order was wrong
        >>> from rtctools.optimization.optimization_problem import OptimizationProblem
    """
    if _preload_failed_due_to_import_order:
        raise RuntimeError(
            "Custom solver preloading was requested via RTCTOOLS_PRELOAD_SOLVER_LIBS "
            "but CasADi was already imported before rtctools could preload the libraries. "
            "This typically happens when importing rtctools submodules directly.\n\n"
            "To fix this, ensure you import rtctools (or set the environment variable) "
            "BEFORE importing any modules that depend on CasADi:\n\n"
            "Bad:\n"
            "  from rtctools.optimization.optimization_problem import OptimizationProblem\n"
            "  # CasADi already loaded, RTCTOOLS_PRELOAD_SOLVER_LIBS ignored\n\n"
            "Good:\n"
            "  import rtctools  # Triggers preloading FIRST\n"
            "  from rtctools.optimization.optimization_problem import OptimizationProblem\n"
        )


def get_solver_library_info(solver_name: str = "highs") -> dict[str, str | Path | int]:
    """
    Get information about which solver library CasADi is using.

    **WARNING**: This function imports CasADi, which prevents any subsequent preloading.
    Only call this AFTER you've completed any custom solver preloading.

    Args:
        solver_name: Name of the solver (e.g., "highs", "ipopt", "bonmin")

    Returns:
        Dictionary with keys:
            - solver: Solver name
            - casadi_version: CasADi version string
            - casadi_path: Path to CasADi installation
            - preloaded: Boolean indicating if custom library was preloaded
            - preloaded_path: Path to preloaded library (only if preloaded=True)
            - casadi_bundled_library_path: Path to CasADi's bundled library (if found)
            - casadi_bundled_library_size: Size of bundled library in bytes (if found)

    Raises:
        RuntimeError: If called before preloading when RTCTOOLS_PRELOAD_SOLVER_LIBS is set

    Example:
        >>> from rtctools.solver_utils import preload_custom_solver_library, get_solver_library_info
        >>> preload_custom_solver_library('/opt/highs/lib/libhighs.so')  # Preload FIRST
        >>> info = get_solver_library_info('highs')  # Safe to call now
        >>> print(f"Using HiGHS from: {info.get('preloaded_path', 'CasADi bundled')}")
    """
    # Check if user is about to sabotage their own preloading
    env_var = os.environ.get("RTCTOOLS_PRELOAD_SOLVER_LIBS", "").strip()
    if env_var and "casadi" not in sys.modules:
        # User has explicitly requested preloading but hasn't done it yet
        # Calling this function now would prevent their custom solver from loading
        raise RuntimeError(
            f"Cannot call get_solver_library_info() before custom solver preloading completes.\n\n"
            f"RTCTOOLS_PRELOAD_SOLVER_LIBS is set to: '{env_var}'\n"
            f"But CasADi has not been imported yet. Calling this function would import CasADi "
            f"and prevent your custom solver from loading.\n\n"
            f"To fix this:\n"
            f"  1. Complete preloading first by importing rtctools or calling "
            f"preload_custom_solver_library()\n"
            f"  2. Then call get_solver_library_info() to verify the preload succeeded\n\n"
            f"Or if you don't actually need custom solvers:\n"
            f"  1. Unset RTCTOOLS_PRELOAD_SOLVER_LIBS environment variable\n"
            f"  2. Then call get_solver_library_info()"
        )

    import casadi as ca

    info = {
        "solver": solver_name,
        "casadi_version": ca.__version__,
        "casadi_path": Path(ca.__file__).parent,
    }

    # Check if preloaded (thread-safe read)
    with _preload_lock:
        if solver_name in _preloaded_solvers:
            info["preloaded"] = True
            info["preloaded_path"] = _preloaded_solvers[solver_name]
        else:
            info["preloaded"] = False

    # Try to find the library file in CasADi directory
    casadi_dir = Path(ca.__file__).parent

    if sys.platform.startswith("win"):
        lib_patterns = [f"lib{solver_name}.dll", f"{solver_name}.dll"]
    elif sys.platform == "darwin":
        lib_patterns = [f"lib{solver_name}.dylib", f"lib{solver_name}.so"]
    else:  # Linux
        lib_patterns = [f"lib{solver_name}.so"]

    for pattern in lib_patterns:
        lib_path = casadi_dir / pattern
        if lib_path.exists():
            info["casadi_bundled_library_path"] = lib_path
            info["casadi_bundled_library_size"] = lib_path.stat().st_size
            break

    return info
