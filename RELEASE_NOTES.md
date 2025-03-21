# Release Notes

## 2.7

### Features

- PIMixin: allow setting the unit of measurement when exporting a timeseries.
- PI: enable writing a timeseries to a given file.
- GoalProgrammingMixin: add aoption to skip a priority.
- Interpolation: add ipopt options to the bspline fit method.

### Fixes / Improvements

- Simulation: improve checks and warning messages when setting initial values.
- ModelicaMixin/Simulation: compile Modelica model again if loading cached file fails.
- CSVMixin: enable support for ensembles with one member.
- Casadi Helpers: fix handling exception in checking if an expression is affine.
- Optimization: do not expand residual functions if this is not possible.

## 2.6

### Features

- Update to Casadi 3.6. This also enables users to use the HiGHS solver.
- Optimization: Add parallellization mode options for collocated integration.
- Optimization: Add a planning mixin (PlanningMixin) that holds marked control variables consistent
    across ensemble members.
- Simulation: Enable using delay equations.
- Simulation: Enable adding custom equations to the model using a python script.
- Simulation: Enable using lookup tables in the model.
- Simulation: Enable selecting a solver for the implicit timestep scheme.

### Fixes / Improvements

- Optimization: Fix and modernise DAE integration for collocoated integration.
- Simulation: support models with an empty DAE.

## 2.5

### Features

- Support for string parameters in Modelica models (parameter string foo = "bar").
- HomotopyMixin: Add support for specifying starting theta
    (e.g. not starting at 0.0, but starting at 0.5 or 1.0).
- Timeseries: Add `__eq__` for easy equality comparison of Timeseries
    (timeseries_a == timeseries_b).

### Fixes / Improvements

- Many speed-ups to SimulationProblem.

### Patches

#### 2.5.2

- Optimization: Enable logging errors for certain priorities as info.
- Fix missing timezone in timeseries_export.xml.
- Simulation: Raise exception when simulation fails.
- Add checks for user-defined simulation/optimization problem class.
- Optimization: Enable optimization problems with time series of length one.
- Improve formatting of XML output.

#### 2.5.1

- Simulation: Various fixes for the time-stepping algorithm.
- Simulation: Enable simulation problems with no parameters.
- Simulation: Enable setting parameters of a simulation problem within the Python script.
- ControlTreeMixin: Enable $k$-ary tress with $k >= 10$.
- ControlTreeMixin: Enable to read ensemble member branches.

## 2.4

### Features

 - New mixin to minimize the absolute value of a function or variable
    (MinAbsGoalProgrammingMixin).
 - New mixin to approximate high order penalties in a linear fashion
    (LinearizedGoalProgrammingMixin).
 - New mixin to read and write from NetCDF files (NetCDFMixin)
 - Convenience method for merging bounds (OptimizationProblem.merge_bounds).
 - Allow passing of arguments to problem class via run_optimization/simulation_problem.
 - Allow passing of model/input/output folder paths to run_optimization/simulation_problem.

### Fixes / Improvements

- Also allow nominals for path and extra variables.
- Many fixes related to (optional) block interpolation of variables.

### Deprecations

- Deprecate explicit collocation.
- Deprecate integrated states.

## 2.3

### Features

- Vector goals.
- Optional more generic/optimal way of translating goals from current priority to the next
    (e.g. `keep_soft_constraints` option).
- Can now provide a custom (initial) seed to SimulationProblem.
- Allow extra variables to appear in path expressions.
- New examples, in particular showing the use (and strength) of using HomotopyMixin for channel flow.

### Fixes / Improvements

- The `scale_by_problem_size` for path goals now only uses number of active time steps.
- Much improved scaling of initial derivatives.
- Improve branch allocation of ControlTreeMixin.
- Fix inconsistencies in internal API w.r.t. what methods can return as symbolic values.
- Many large and small optimizations and refactorings for performance.
- Sanity checks on goals, e.g. function ranges.
    Some models may fail the checks now,
    but if they do the goal in question did not make much sense anyway.

## 2.2

- Various new features and improvements.
- Rename pymola to pymoca.

## 2.1

- Various new features and improvements.
- Upgrade to Python 3.
- Use pymola instead of JModelica.

## 2.0

First release in 2.x series.
