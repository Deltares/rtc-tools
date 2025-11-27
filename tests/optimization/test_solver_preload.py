"""Tests for custom solver library preloading functionality.

These are UNIT tests that use mocking to test the preloading mechanism.

For INTEGRATION tests that verify actual library loading with CasADi, see:
    tests/optimization/test_solver_preload_integration.py

Integration tests cannot be part of the pytest suite because:
1. CasADi is already imported by other tests before these run
2. Python cannot truly reload C extension modules
3. Preloading only works BEFORE CasADi's first import in a process
"""

import ctypes
import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from rtctools.solver_utils import (
    _preload_solvers_from_environment,
    check_preload_import_order,
    get_solver_library_info,
    preload_custom_solver_library,
)

from ..test_case import TestCase


class TestSolverPreloadExplicit(TestCase):
    """Test explicit preloading via function calls."""

    def setUp(self) -> None:
        # Clear any previously preloaded solvers for clean tests
        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preloaded_solvers.clear()

    def test_preload_nonexistent_file(self) -> None:
        """Test that preloading a nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            preload_custom_solver_library("/nonexistent/path/libhighs.so", "HiGHS")

    @patch("ctypes.CDLL")
    def test_preload_success_linux(self, mock_cdll) -> None:
        """Test successful preloading on Linux."""
        # Create a temporary file to simulate library
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch("sys.platform", "linux"):
                result = preload_custom_solver_library(tmp_path, "test_solver")
                self.assertTrue(result)
                # Verify CDLL was called with RTLD_GLOBAL mode
                mock_cdll.assert_called_once()
                call_args = mock_cdll.call_args
                self.assertIn("mode", call_args[1])
                self.assertEqual(call_args[1]["mode"], ctypes.RTLD_GLOBAL)
        finally:
            os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    def test_preload_success_windows(self, mock_cdll) -> None:
        """Test successful preloading on Windows."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".dll", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch("sys.platform", "win32"):
                result = preload_custom_solver_library(tmp_path, "test_solver")
                self.assertTrue(result)
                # Verify CDLL was called with winmode=0
                mock_cdll.assert_called_once()
                call_args = mock_cdll.call_args
                self.assertEqual(call_args[1]["winmode"], 0)
        finally:
            os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    def test_preload_duplicate(self, mock_cdll) -> None:
        """Test that duplicate preloading is handled correctly."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # First preload
            result1 = preload_custom_solver_library(tmp_path, "test_solver")
            self.assertTrue(result1)

            # Second preload of same library - should return True without re-loading
            result2 = preload_custom_solver_library(tmp_path, "test_solver")
            self.assertTrue(result2)
            # CDLL should only be called once
            self.assertEqual(mock_cdll.call_count, 1)
        finally:
            os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    def test_preload_different_paths_same_solver(self, mock_cdll) -> None:
        """Test that preloading from different paths for same solver name is rejected."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path1 = Path(tmpdir) / "lib1.so"
            tmp_path2 = Path(tmpdir) / "lib2.so"
            tmp_path1.touch()
            tmp_path2.touch()

            # First preload
            result1 = preload_custom_solver_library(tmp_path1, "test_solver")
            self.assertTrue(result1)

            # Second preload from different path - should be rejected
            result2 = preload_custom_solver_library(tmp_path2, "test_solver")
            self.assertFalse(result2)
            # CDLL should only be called once
            self.assertEqual(mock_cdll.call_count, 1)

    @patch("ctypes.CDLL", side_effect=OSError("Mock load failure"))
    def test_preload_failure(self, mock_cdll) -> None:
        """Test that loading failure raises RuntimeError with helpful message."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with self.assertRaises(RuntimeError) as context:
                preload_custom_solver_library(tmp_path, "test_solver")

            # Check error message contains helpful information
            error_msg = str(context.exception)
            self.assertIn("Failed to preload", error_msg)
            self.assertIn("Common causes", error_msg)
            self.assertIn("dependencies", error_msg.lower())
        finally:
            os.unlink(tmp_path)


class TestSolverPreloadEnvironment(TestCase):
    """Test automatic preloading via environment variable."""

    def setUp(self) -> None:
        # Clear any previously preloaded solvers
        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preloaded_solvers.clear()
        # Clear environment variable
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def tearDown(self) -> None:
        # Clean up environment
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def test_no_environment_variable(self) -> None:
        """Test that nothing happens when environment variable is not set."""
        _preload_solvers_from_environment()
        import rtctools.solver_utils

        self.assertEqual(len(rtctools.solver_utils._preloaded_solvers), 0)

    def test_empty_environment_variable(self) -> None:
        """Test that empty environment variable is handled gracefully."""
        os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = ""
        _preload_solvers_from_environment()
        import rtctools.solver_utils

        self.assertEqual(len(rtctools.solver_utils._preloaded_solvers), 0)

    @patch("ctypes.CDLL")
    @patch.dict("sys.modules", {"casadi": None}, clear=False)
    def test_single_solver_from_environment(self, mock_cdll) -> None:
        """Test loading a single solver from environment variable."""
        import tempfile

        # Remove casadi from sys.modules to simulate fresh import
        sys.modules.pop("casadi", None)

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = f"test_solver:{tmp_path}"
            _preload_solvers_from_environment()

            import rtctools.solver_utils

            self.assertIn("test_solver", rtctools.solver_utils._preloaded_solvers)
            mock_cdll.assert_called_once()
        finally:
            os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    @patch.dict("sys.modules", {"casadi": None}, clear=False)
    def test_multiple_solvers_from_environment(self, mock_cdll) -> None:
        """Test loading multiple solvers from environment variable."""
        import tempfile

        # Remove casadi from sys.modules to simulate fresh import
        sys.modules.pop("casadi", None)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path1 = Path(tmpdir) / "lib1.so"
            tmp_path2 = Path(tmpdir) / "lib2.so"
            tmp_path1.touch()
            tmp_path2.touch()

            os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = f"solver1:{tmp_path1},solver2:{tmp_path2}"
            _preload_solvers_from_environment()

            import rtctools.solver_utils

            self.assertIn("solver1", rtctools.solver_utils._preloaded_solvers)
            self.assertIn("solver2", rtctools.solver_utils._preloaded_solvers)
            self.assertEqual(mock_cdll.call_count, 2)

    def test_invalid_format(self) -> None:
        """Test that invalid format is logged but doesn't crash."""
        os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = "invalid_no_colon"
        # Should not raise exception
        _preload_solvers_from_environment()

        import rtctools.solver_utils

        self.assertEqual(len(rtctools.solver_utils._preloaded_solvers), 0)

    @patch("ctypes.CDLL")
    def test_explicit_preload_takes_precedence(self, mock_cdll) -> None:
        """Test that explicit preloading takes precedence over environment variable."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path1 = Path(tmpdir) / "lib1.so"
            tmp_path2 = Path(tmpdir) / "lib2.so"
            tmp_path1.touch()
            tmp_path2.touch()

            # Explicit preload first
            preload_custom_solver_library(tmp_path1, "test_solver")

            # Set environment variable with different path
            os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = f"test_solver:{tmp_path2}"
            _preload_solvers_from_environment()

            import rtctools.solver_utils

            # Should still be using the explicitly preloaded path
            self.assertEqual(
                Path(rtctools.solver_utils._preloaded_solvers["test_solver"]).resolve(),
                tmp_path1.resolve(),
            )
            # CDLL should only be called once (for explicit preload)
            self.assertEqual(mock_cdll.call_count, 1)

    def test_nonexistent_file_from_environment(self) -> None:
        """Test that nonexistent file from environment is logged but doesn't crash."""
        os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = "test_solver:/nonexistent/path.so"
        # Should not raise exception (graceful degradation)
        _preload_solvers_from_environment()

        import rtctools.solver_utils

        self.assertEqual(len(rtctools.solver_utils._preloaded_solvers), 0)


class TestImportOrderGuard(TestCase):
    """Test import order detection and guard function."""

    def setUp(self) -> None:
        # Clear any previously preloaded solvers
        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preloaded_solvers.clear()
            rtctools.solver_utils._preload_failed_due_to_import_order = False
        # Clear environment variable
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def tearDown(self) -> None:
        # Clean up
        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preload_failed_due_to_import_order = False
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def test_check_preload_import_order_success(self) -> None:
        """Test that check passes when no import order issue."""
        # Should not raise
        check_preload_import_order()

    def test_check_preload_import_order_failure(self) -> None:
        """Test that check raises when import order is wrong."""
        import rtctools.solver_utils

        # Simulate failed preload due to import order
        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preload_failed_due_to_import_order = True

        with self.assertRaises(RuntimeError) as context:
            check_preload_import_order()

        error_msg = str(context.exception)
        self.assertIn("Custom solver preloading was requested", error_msg)
        self.assertIn("CasADi was already imported", error_msg)
        self.assertIn("import", error_msg.lower())

    def test_preload_from_environment_sets_flag_on_casadi_already_imported(self) -> None:
        """Test that flag is set when CasADi is already imported."""
        import rtctools.solver_utils

        # Set environment variable
        os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = "highs:/fake/path.so"

        # Simulate CasADi already being imported
        sys.modules["casadi"] = MagicMock()

        try:
            _preload_solvers_from_environment()

            # Flag should be set
            self.assertTrue(rtctools.solver_utils._preload_failed_due_to_import_order)

            # check_preload_import_order should now raise
            with self.assertRaises(RuntimeError):
                check_preload_import_order()
        finally:
            # Clean up fake casadi module
            del sys.modules["casadi"]


class TestSolverLibraryInfo(TestCase):
    """Test diagnostic utility for getting solver library information."""

    def setUp(self) -> None:
        # Clear environment variable
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def tearDown(self) -> None:
        # Clean up
        if "RTCTOOLS_PRELOAD_SOLVER_LIBS" in os.environ:
            del os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"]

    def test_get_highs_info(self) -> None:
        """Test getting HiGHS library information."""
        info = get_solver_library_info("highs")

        # Check required keys
        self.assertIn("solver", info)
        self.assertIn("casadi_version", info)
        self.assertIn("casadi_path", info)
        self.assertIn("preloaded", info)

        self.assertEqual(info["solver"], "highs")
        self.assertIsInstance(info["preloaded"], bool)

    def test_get_info_raises_if_called_before_env_var_preload(self) -> None:
        """Test that calling get_solver_library_info before preloading raises error."""
        # Set environment variable
        os.environ["RTCTOOLS_PRELOAD_SOLVER_LIBS"] = "highs:/fake/path.so"

        # Simulate casadi NOT being imported yet
        casadi_was_imported = "casadi" in sys.modules
        if casadi_was_imported:
            # Can't test this scenario in this test run since casadi is already loaded
            # This would only trigger in a fresh Python process
            self.skipTest("CasADi already imported - can't test pre-import error")

        # Should raise RuntimeError to prevent sabotaging preload
        with self.assertRaises(RuntimeError) as context:
            get_solver_library_info("highs")

        error_msg = str(context.exception)
        self.assertIn("Cannot call get_solver_library_info()", error_msg)
        self.assertIn("RTCTOOLS_PRELOAD_SOLVER_LIBS is set", error_msg)
        self.assertIn("prevent your custom solver from loading", error_msg)

    def test_get_info_for_unknown_solver(self) -> None:
        """Test getting info for a solver that doesn't exist."""
        info = get_solver_library_info("nonexistent_solver")

        # Should still return basic info
        self.assertIn("solver", info)
        self.assertIn("casadi_version", info)
        self.assertEqual(info["solver"], "nonexistent_solver")
        # Should not have library_path since it doesn't exist
        self.assertNotIn("casadi_bundled_library_path", info)

    @patch("ctypes.CDLL")
    def test_get_info_after_preload(self, mock_cdll) -> None:
        """Test that info reflects preloaded library."""
        import tempfile

        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preloaded_solvers.clear()

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            preload_custom_solver_library(tmp_path, "test_solver")
            info = get_solver_library_info("test_solver")

            self.assertTrue(info["preloaded"])
            self.assertEqual(info["preloaded_path"], Path(tmp_path))
        finally:
            os.unlink(tmp_path)


class TestThreadSafety(TestCase):
    """Test thread-safety of preloading operations."""

    def setUp(self) -> None:
        # Clear any previously preloaded solvers
        import rtctools.solver_utils

        with rtctools.solver_utils._preload_lock:
            rtctools.solver_utils._preloaded_solvers.clear()

    @patch("ctypes.CDLL")
    def test_concurrent_preload_same_library(self, mock_cdll) -> None:
        """Test that concurrent preloads of the same library are handled safely."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            results = []
            errors = []

            def preload_worker():
                try:
                    result = preload_custom_solver_library(tmp_path, "test_solver")
                    results.append(result)
                except Exception as e:
                    errors.append(e)

            # Launch 5 threads trying to preload the same library
            threads = [threading.Thread(target=preload_worker) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # No errors should occur
            self.assertEqual(len(errors), 0)

            # All threads should succeed (first gets True, rest get True from duplicate check)
            self.assertEqual(len(results), 5)
            self.assertTrue(all(results))

            # CDLL should only be called once (first thread wins)
            self.assertEqual(mock_cdll.call_count, 1)
        finally:
            os.unlink(tmp_path)

    @patch("ctypes.CDLL")
    def test_concurrent_preload_different_libraries(self, mock_cdll) -> None:
        """Test that concurrent preloads of different libraries work correctly."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple temp files
            temp_files = []
            for i in range(3):
                tmp_path = Path(tmpdir) / f"lib{i}.so"
                tmp_path.touch()
                temp_files.append((str(tmp_path), f"solver_{i}"))

            results = {}
            errors = []

            def preload_worker(path, name):
                try:
                    result = preload_custom_solver_library(path, name)
                    results[name] = result
                except Exception as e:
                    errors.append(e)

            # Launch threads for different solvers
            threads = [
                threading.Thread(target=preload_worker, args=(path, name))
                for path, name in temp_files
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # No errors should occur
            self.assertEqual(len(errors), 0)

            # All solvers should be preloaded successfully
            self.assertEqual(len(results), 3)
            self.assertTrue(all(results.values()))

            # CDLL should be called once per solver
            self.assertEqual(mock_cdll.call_count, 3)


class TestRealHiGHSPreload(TestCase):
    """Integration test with real HiGHS 1.12.0 library.

    Note: This test is skipped by default because the MSYS2 HiGHS 1.12.0 library
    has missing dependencies (libgcc, libstdc++, etc.) that cause load failures.
    This is expected behavior and was documented during our investigation.

    The test exists to document the expected behavior and can be enabled
    when a properly bundled HiGHS library (with all dependencies) is available.

    Environment Variables:
        TEST_HIGHS_LIBRARY_PATH: Optional path to custom HiGHS library for testing.
                                If not set, uses platform-specific default under test_highs_custom/
    """

    def setUp(self) -> None:
        # Path to the extracted HiGHS 1.12.0 library
        # Can be overridden with TEST_HIGHS_LIBRARY_PATH environment variable
        custom_path = os.environ.get("TEST_HIGHS_LIBRARY_PATH")
        if custom_path:
            self.custom_highs_path = Path(custom_path)
        else:
            # Platform-specific default path
            base_dir = Path(__file__).parent.parent.parent / "test_highs_custom"
            if sys.platform.startswith("win"):
                self.custom_highs_path = base_dir / "mingw64" / "bin" / "libhighs.dll"
            elif sys.platform == "darwin":
                self.custom_highs_path = base_dir / "macos" / "lib" / "libhighs.dylib"
            else:
                self.custom_highs_path = base_dir / "linux" / "lib" / "libhighs.so"

    @unittest.skip("MSYS2 HiGHS 1.12.0 has missing dependencies - expected failure")
    def test_real_highs_preload(self) -> None:
        """Test preloading actual HiGHS 1.12.0 library.

        This test is skipped because the MSYS2-built HiGHS requires MinGW runtime
        DLLs (libgcc, libstdc++, libwinpthread) which are not bundled.

        To make this test pass, users would need to:
        1. Use a statically-linked HiGHS build, OR
        2. Ensure MinGW runtime DLLs are in PATH, OR
        3. Extract all dependencies from the MSYS2 package
        """
        if not self.custom_highs_path.exists():
            self.skipTest(f"Custom HiGHS library not found at {self.custom_highs_path}")

        # This will raise RuntimeError due to missing dependencies
        with self.assertRaises(RuntimeError) as context:
            preload_custom_solver_library(str(self.custom_highs_path), "HiGHS")

        # Verify error message is helpful
        error_msg = str(context.exception)
        self.assertIn("Failed to preload", error_msg)
        self.assertIn("dependencies", error_msg.lower())
