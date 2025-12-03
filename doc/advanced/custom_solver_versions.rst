Using Custom Solver Versions
=============================

By default, RTC-Tools uses the solver libraries bundled with CasADi. However, you may need to use different versions of solvers like HiGHS, IPOPT, or others for various reasons:

* **Performance improvements** in newer solver releases
* **Bug fixes** available in specific versions
* **New features** not yet in CasADi's bundled version
* **Custom builds** optimized for your hardware or compiled with specific options
* **Version consistency** across development and production environments

This guide explains how to use custom solver library versions with RTC-Tools.

.. warning::
   Custom solver libraries must be ABI-compatible with CasADi's expectations. Using incompatible builds may cause crashes or unexpected behavior.

How It Works
------------

There are multiple ways to preload custom solver libraries before CasADi loads its bundled versions:

1. **Native OS preloading** (Linux/macOS) - Uses standard ``LD_PRELOAD`` or ``DYLD_INSERT_LIBRARIES``
2. **RTC-Tools Python preloading** (Cross-platform) - Uses Python's ``ctypes`` module with the ``RTCTOOLS_PRELOAD_SOLVER_LIBS`` environment variable
3. **Direct ctypes** (Windows fallback) - Manual ``ctypes.CDLL()`` call in your script

Method 1: Native OS Preloading (Linux/macOS Only)
--------------------------------------------------

On Linux and macOS, you can use the operating system's native library preloading mechanisms. This is often the simplest approach for these platforms.

**Linux:**

.. code-block:: bash

   LD_PRELOAD=/opt/highs-1.12/lib/libhighs.so.1 python my_optimization_script.py

**macOS:**

.. code-block:: bash

   DYLD_INSERT_LIBRARIES=/opt/highs-1.12/lib/libhighs.dylib python my_optimization_script.py

.. note::
   This method only works on Linux and macOS. Windows does not have an equivalent mechanism.

Method 2: RTC-Tools Environment Variable (Cross-Platform)
----------------------------------------------------------

For a cross-platform solution, use the ``RTCTOOLS_PRELOAD_SOLVER_LIBS`` environment variable. This works on Linux, macOS, and Windows.

**Linux/macOS:**

.. code-block:: bash

   export RTCTOOLS_PRELOAD_SOLVER_LIBS="highs:/opt/highs-1.12/lib/libhighs.so"
   python my_optimization_script.py

**Windows:**

.. code-block:: batch

   set RTCTOOLS_PRELOAD_SOLVER_LIBS=highs:C:\highs-1.12\bin\libhighs.dll
   python my_optimization_script.py

To make MinGW-built solvers work, ensure the required runtime DLLs
(``libgcc_s_seh-1.dll``, ``libstdc++-6.dll``, ``libwinpthread-1.dll``, etc.) are
available when the library loads. You can either add the directory containing
those DLLs to your ``PATH`` environment variable, or copy the DLLs into the same
directory as ``libhighs.dll`` so they are discovered alongside the solver.

**Multiple Solvers:**

.. code-block:: bash

   export RTCTOOLS_PRELOAD_SOLVER_LIBS="highs:/path/libhighs.so,ipopt:/path/libipopt.so"

**Docker/Container Environments:**

.. code-block:: dockerfile

   FROM python:3.11

   # Install custom HiGHS solver
   COPY libhighs.so /opt/highs/lib/

   # Set environment variable for RTC-Tools
   ENV RTCTOOLS_PRELOAD_SOLVER_LIBS="highs:/opt/highs/lib/libhighs.so"

   # Install RTC-Tools
   RUN pip install rtc-tools

   # Your application code
   COPY . /app
   WORKDIR /app
   CMD ["python", "run_optimization.py"]

Method 3: Direct ctypes Call (Windows/Development)
---------------------------------------------------

For Windows without environment variables, or for development/testing, you can manually preload in your Python code:

.. code-block:: python

   import ctypes

   # Windows example
   ctypes.CDLL(r"C:\highs-1.12\bin\libhighs.dll")

   # Now import RTC-Tools
   import rtctools
   from rtctools.optimization.collocated_integrated_optimization_problem import (
       CollocatedIntegratedOptimizationProblem
   )

Method 4: Explicit Function Call (Recommended for Development)
---------------------------------------------------------------

For more control, explicitly preload in your Python code before importing optimization modules:

.. code-block:: python

   from rtctools.solver_utils import preload_custom_solver_library

   # Preload BEFORE importing any optimization modules
   preload_custom_solver_library('/opt/highs-1.12/lib/libhighs.so', 'HiGHS')

   # Now import and use optimization modules
   from rtctools.optimization.collocated_integrated_optimization_problem import (
       CollocatedIntegratedOptimizationProblem
   )

   class MyProblem(CollocatedIntegratedOptimizationProblem):
       def solver_options(self):
           options = super().solver_options()
           options['solver'] = 'highs'
           return options
       # ... rest of implementation

   problem = MyProblem()
   problem.optimize()

Verifying Custom Solver is Used
--------------------------------

Use ``get_solver_library_info()`` to confirm preloading succeeded:

.. code-block:: python

   from rtctools.solver_utils import get_solver_library_info

   info = get_solver_library_info('highs')

   if info['preloaded']:
       print(f"✓ Using custom HiGHS from: {info['preloaded_path']}")
   else:
       print("✗ Using CasADi bundled HiGHS")
       if 'casadi_bundled_library_path' in info:
           print(f"  Bundled library: {info['casadi_bundled_library_path']}")

Troubleshooting
---------------

**FileNotFoundError: Solver library not found**

The path is wrong or the file is unreadable. Verify the path, make sure the file exists, and confirm it has read permissions.

**RuntimeError: Failed to preload**

Usually indicates missing dependencies or an ABI mismatch. Check for missing libraries with ``ldd`` (Linux) or ``otool -L`` (macOS), use the `Dependencies <https://github.com/lucasg/Dependencies>`_ tool on Windows, and confirm the build matches CasADi's compiler, bitness, and C++ runtime.

**"CasADi already imported" warning**

CasADi loads before preloading runs (for example, after importing ``rtctools.optimization`` directly). Import ``rtctools`` or call ``preload_custom_solver_library()`` before any CasADi-dependent modules. Use ``check_preload_import_order()`` if you want the process to fail fast when the order is wrong.

**Solver still reports bundled version**

Check logs for preload errors, confirm the import order, and inspect ``get_solver_library_info()`` for the active paths.

**Segmentation fault or crash**

This indicates ABI incompatibility between your custom solver and CasADi. Common causes:

* **Compiler mismatch**: Custom solver built with a different compiler than CasADi (e.g., GCC vs Intel vs MSVC)
* **C++ runtime mismatch**: Different C++ standard library versions or ABIs
* **Bitness mismatch**: Mixing 32-bit and 64-bit libraries
* **Missing dependencies**: Solver depends on libraries not available at runtime

To diagnose:

1. Check CasADi's compiler: ``python -c "import casadi; print(casadi.CasadiMeta.compiler())"``
2. Verify your custom solver was built with the same compiler toolchain
3. Check for missing dependencies: ``ldd`` (Linux), ``otool -L`` (macOS), or Dependencies tool (Windows)
4. If the issue persists, fall back to CasADi's bundled version or build the solver from source with matching toolchain

Compatibility Notes
-------------------

.. warning::
   **ABI Compatibility is Critical**: Custom solver libraries must match CasADi's build configuration (compiler, C++ runtime, bitness). Incompatible builds may cause:

   * Segmentation faults (crashes)
   * Silent data corruption
   * Incorrect optimization results

   Always test thoroughly before using custom solver versions in production. If you experience crashes, verify that your custom solver was built with the same compiler toolchain as CasADi's bundled solvers.

Currently supported and tested solver: **HiGHS**

* **HiGHS**: Validated with this guide; C API has been stable since v1.7.0. Known to work with versions 1.7.x through 1.12.x when built with compatible toolchains.
* **IPOPT on Windows**: Preloading does not work with precompiled binaries - publicly available IPOPT binaries are compiled with Intel compilers while CasADi's Windows wheels use GCC/MinGW, causing ABI incompatibility. Julia's GCC-compiled IPOPT binaries also fail due to missing dependencies. Workaround: use preloading in a Linux environment (e.g., Docker, WSL2, native Linux) with conda-forge GCC-compiled IPOPT binaries.
* **Other solvers** (BONMIN, CBC, etc.): May work with the same approach, but have not been officially tested. Validate thoroughly before relying on them in production.
* Requires Python 3.7+ (``ctypes`` standard library) and CasADi 3.6.0 or newer for the preload hooks used here.

Solver Coverage
^^^^^^^^^^^^^^^

We have confirmed this workflow with HiGHS. If you preload other solvers (IPOPT, BONMIN, CBC, etc.), treat them as experimental and perform end-to-end validation. Commercial solvers typically ship their own integration tooling and may not benefit from this preload pathway.

Testing Your Setup
------------------

RTC-Tools includes a standalone integration test script:

.. code-block:: bash

   python tests/optimization/test_solver_preload_integration.py

Run it in a fresh Python process since CasADi cannot be reloaded once imported.

Best Practices
--------------

1. **Test thoroughly** - Verify your custom solver produces correct results with your models
2. **Verify preloading** - Use ``get_solver_library_info()`` to confirm custom library loaded
3. **Document versions** - Keep records of which solver versions work with your application
4. **Use environment variables in production** - Easier to manage in deployment pipelines
5. **Version pin** - Specify exact solver versions in your documentation
6. **Container builds** - Include custom solvers in Docker images for reproducibility
7. **CI/CD integration** - Test with custom solvers in continuous integration

API Reference
-------------

.. py:function:: preload_custom_solver_library(library_path, solver_name=None)

   Preload a custom solver library before CasADi imports it.

   :param library_path: Path to the solver library file (str or Path)
   :param solver_name: Optional solver name for logging (default: derived from filename)
   :return: True if successful or already loaded from same path; False if already loaded from different path
   :raises FileNotFoundError: If library file doesn't exist
   :raises RuntimeError: If library fails to load

   Must be called before importing casadi or any module that imports CasADi.

.. py:function:: check_preload_import_order()

   Check if custom solver preloading was requested but failed due to import order.

   :raises RuntimeError: If preloading was requested but CasADi was already imported

   This function can be called by user code to enforce strict checking of import order
   when custom solver preloading is critical. By default, RTC-Tools only logs a warning
   when import order prevents preloading.

.. py:function:: get_solver_library_info(solver_name='highs')

   Get information about which solver library CasADi is using.

   :param solver_name: Name of the solver (e.g., 'highs', 'ipopt', 'bonmin')
   :return: Dictionary with solver information including paths, versions, and preload status
   :raises RuntimeError: If called before preloading when RTCTOOLS_PRELOAD_SOLVER_LIBS is set

   .. warning::
      This function imports CasADi, which prevents any subsequent preloading.
      Only call this AFTER you've completed any custom solver preloading.
      If RTCTOOLS_PRELOAD_SOLVER_LIBS is set but CasADi hasn't been imported yet,
      calling this function will raise RuntimeError to prevent sabotaging the preload.

.. py:data:: RTCTOOLS_PRELOAD_SOLVER_LIBS

   Environment variable for automatic solver preloading.

   **Format:** ``"solver_name:path,solver_name:path,..."``

   **Example:** ``"highs:/opt/highs/lib/libhighs.so,ipopt:/usr/lib/libipopt.so"``

   Processed automatically when rtctools is imported.
