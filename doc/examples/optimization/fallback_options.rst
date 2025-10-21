Fallback Options: Using a Different Solver When the Previous One Failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This example focuses on how to implement a fallback option in RTC-Tools.
    It assumes basic exposure to RTC-Tools.
    If you are a first-time user of RTC-Tools, see :doc:`basic`.

If a solver fails to find a solution, you can fall back to a different solver.
The following example shows how this can be automated
by overwriting the ``optimize`` and ``solver_options`` method
of an ``OptimizationProblem`` class.
After that, an example is given for how to include a fallback option when using goal programming.


Implementing a Basic Fallback Option
------------------------------------

A fallback option to fall back to a different solver if the previous one failed,
can be implemented in the following way:

* Add a ``solver`` attribute to your ``OptimizationProblem`` class
  to keep track of the solver that is used.
* Overwrite the ``optimize`` method of your optimization problem class,
  to loop over a list of solvers until one of them succeeds.
* Overwrite the ``solver_options`` method of your optimization problem class,
  to select the correct solver options for the current ``solver``.

To add a ``solver`` attribute, we can overwrite the ``__init__`` method
of our optimization problem class:

.. literalinclude:: ../../../examples/fallback_option/src/example.py
  :language: python
  :pyobject: Example.__init__
  :lineno-match:

Here, we set the ``solver`` attribute initially to ``None``.

To iterate over a list of solvers, we can overwrite the ``optimize`` method:

.. literalinclude:: ../../../examples/fallback_option/src/example.py
  :language: python
  :pyobject: Example.optimize
  :lineno-match:

Here, we iterate over the solvers `ipopt` and `highs`.
In case the solver succeeds, we break out of the loop.

To select the correct solver options, we overwrite the ``solver_options`` method:

.. literalinclude:: ../../../examples/fallback_option/src/example.py
  :language: python
  :pyobject: Example.solver_options
  :lineno-match:

Here, the correct solver options are chosen based on the selected solver.

The script of the entire example is as follows:

.. literalinclude:: ../../../examples/fallback_option/src/example.py
  :language: python
  :lineno-match:

The ``DummySolver`` class forces the solver to only succeed if it is `highs`
and is only added for illustration purposes.

Implementing a Fallback Option When Using Goal Programming
----------------------------------------------------------

When using goal programming, a solver might fail for a specific priority
and you might want to fall back to a different solver for just this priority.
To implement this, we need the following:

* Create ``MultiRunMixin`` class that inherits from ``OptimizationProblem``
  and overwrites the ``optimize`` method to loop over a list of solvers
  until one of them succeeds.
* Let your main optimization problem class also inherit from ``MultiRunMixin``.
  It is important that ``MultiRunMixin`` comes after ``GoalProgrammingMixin``
  in the inheritance list.
  This ensures that the ``optimize`` method of ``MultiRunMixin`` is called
  within the ``optimize`` method of ``GoalProgrammingMixin``
  and thus that we loop over all solvers for each priority.
* Overwrite the ``solver_options`` method of your main optimization problem class,
  to select the correct solver options for the current ``solver``.

The ``MultiRunMixin`` class, can look somethling like this:

.. literalinclude:: ../../../examples/fallback_option/src/example_with_gp.py
  :language: python
  :pyobject: MultiRunMixin
  :lineno-match:

It has an attribute `solver` that keeps track of the current solver.
During optimization, it iterates over the solvers `ipopt` and `highs`
and breaks out of the loop in case a solver succeeds.

The main optimization problem class inherits from ``GoalProgrammingMixin``
and ``MultiRunMixin``:

.. literalinclude:: ../../../examples/fallback_option/src/example_with_gp.py
  :language: python
  :pyobject: Example
  :lineno-match:
  :end-before: """

It is important that ``MultiRunMixin`` comes after ``GoalProgrammingMixin``
so that the ``optimize`` method of ``MultiRunMixin`` is called
within the ``optimize`` method of ``GoalProgrammingMixin``.

As before, the main optimization problem class
also overwrites the ``solver_options`` method to select the correct solver options:

.. literalinclude:: ../../../examples/fallback_option/src/example_with_gp.py
  :language: python
  :pyobject: Example.solver_options
  :lineno-match:

The script of the entire example is as follows:

.. literalinclude:: ../../../examples/fallback_option/src/example_with_gp.py
  :language: python
  :lineno-match:

The ``DummySolver`` class forces the solver to only succeed if it is `highs`
and is only added for illustration purposes.
The ``DummyGoal`` is also only added for illustration purposes.
