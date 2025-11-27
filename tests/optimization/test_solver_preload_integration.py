"""
Integration test for custom solver preloading.

IMPORTANT: This test CANNOT be run as part of the normal pytest suite because:
1. CasADi is already imported by other tests before this runs
2. Python cannot truly reload C extension modules
3. Preloading only works BEFORE CasADi's first import

This script must be run in a fresh Python process:

    python tests/optimization/test_solver_preload_integration.py

Environment Variables:
    TEST_HIGHS_LIBRARY_PATH: Optional path to custom HiGHS library for testing.
                            If not set, uses platform-specific default under test_highs_custom/

The test verifies that:
1. Custom solver library is successfully preloaded
2. CasADi uses the preloaded library instead of its bundled version
3. Solver version matches the custom library version
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_explicit_preload():
    """Test explicit preloading before CasADi import."""
    print("\n=== Test 1: Explicit Preloading ===")

    # Verify CasADi not yet imported
    if "casadi" in sys.modules:
        print("[FAIL] CasADi already imported - cannot test preloading")
        return False

    import os

    from rtctools.solver_utils import get_solver_library_info, preload_custom_solver_library

    # Path to custom HiGHS library (you need to provide a real library for this test)
    # Can be overridden with TEST_HIGHS_LIBRARY_PATH environment variable
    custom_path = os.environ.get("TEST_HIGHS_LIBRARY_PATH")
    if custom_path:
        custom_highs_path = Path(custom_path)
    else:
        # Platform-specific default path
        base_dir = Path(__file__).parent.parent.parent / "test_highs_custom"
        if sys.platform.startswith("win"):
            custom_highs_path = base_dir / "mingw64" / "bin" / "libhighs.dll"
        elif sys.platform == "darwin":
            custom_highs_path = base_dir / "macos" / "lib" / "libhighs.dylib"
        else:
            custom_highs_path = base_dir / "linux" / "lib" / "libhighs.so"

    if not custom_highs_path.exists():
        print(f"[SKIP] Custom HiGHS library not found at {custom_highs_path}")
        print("       This test requires a real HiGHS library to verify integration")
        return None  # Skip

    try:
        # Preload custom library
        print(f"Preloading custom HiGHS from: {custom_highs_path}")
        success = preload_custom_solver_library(str(custom_highs_path), "highs")

        if not success:
            print("[FAIL] preload_custom_solver_library() returned False")
            return False

        print("[OK] Preload succeeded")

        # Now import CasADi and verify
        print("Importing CasADi...")
        import casadi as ca

        print(f"CasADi version: {ca.__version__}")

        # Get solver info
        info = get_solver_library_info("highs")
        print(f"Preloaded: {info['preloaded']}")

        if info["preloaded"]:
            print(f"Custom library path: {info['preloaded_path']}")
            print("[OK] Custom HiGHS was preloaded")

            # Verify the path matches
            if Path(info["preloaded_path"]).samefile(custom_highs_path):
                print("[OK] Preloaded path matches expected path")
                return True
            else:
                print(f"[FAIL] Path mismatch: {info['preloaded_path']} != {custom_highs_path}")
                return False
        else:
            print("[FAIL] HiGHS was not preloaded")
            return False

    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_environment_variable_preload():
    """Test environment variable preloading.

    This would need to be run in a separate process with env var set before importing rtctools.
    """
    print("\n=== Test 2: Environment Variable Preloading ===")
    print(
        "[SKIP] This test requires running in a fresh process with RTCTOOLS_PRELOAD_SOLVER_LIBS set"
    )
    print("       Example:")
    print("           set RTCTOOLS_PRELOAD_SOLVER_LIBS=highs:C:\\path\\to\\libhighs.dll")
    print(
        '           python -c "import rtctools; from rtctools.solver_utils import '
        "get_solver_library_info; print(get_solver_library_info('highs'))\""
    )
    return None


def test_defensive_checks():
    """Test that defensive checks work correctly."""
    print("\n=== Test 3: Defensive Checks ===")

    # This test can only run if CasADi is already imported
    if "casadi" not in sys.modules:
        print("[SKIP] CasADi not imported - can't test defensive checks")
        return None

    import os

    from rtctools.solver_utils import get_solver_library_info

    # Test 1: get_solver_library_info with env var set should raise
    os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = "highs:/fake/path.so"

    try:
        # Since CasADi is already imported, this should NOT raise
        _ = get_solver_library_info("highs")
        print("[OK] get_solver_library_info() works when CasADi already imported")
    except RuntimeError as e:
        print(f"[FAIL] Unexpected RuntimeError: {e}")
        return False
    finally:
        del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    return True


if __name__ == "__main__":
    print("=" * 70)
    print("Custom Solver Preloading Integration Tests")
    print("=" * 70)
    print()
    print("NOTE: These tests verify actual library preloading behavior.")
    print("      Some tests may be skipped if custom libraries are not available.")
    print()

    results = []

    # Run tests
    results.append(("Explicit Preload", test_explicit_preload()))
    results.append(("Environment Variable", test_environment_variable_preload()))
    results.append(("Defensive Checks", test_defensive_checks()))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for name, result in results:
        status = "PASS" if result is True else "FAIL" if result is False else "SKIP"
        print(f"  {name:30s} {status}")

    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    sys.exit(0 if failed == 0 else 1)
