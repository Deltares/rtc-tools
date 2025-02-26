Using an Ensemble Forecast
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    This example is an extension of :doc:`lookup_table`. It
    assumes prior knowledge of goal programming and the lookup tables components
    of RTC-Tools. If you are a first-time user of RTC-Tools, see
    :doc:`basic`.

Then biggest change to RTC-Tools when using an ensemble is the structure of the
directory. The folder ``<examples directory>\ensemble``
contains a complete RTC-Tools ensemble optimization problem. An RTC-Tools
ensemble directory has the following structure:

* ``model``: This folder contains the Modelica model. The Modelica model
  contains the physics of the RTC-Tools model.
* ``src``: This folder contains a Python file. This file contains the
  configuration of the model and is used to run the model.
* ``input``: This folder contains the model input data pertaining to each
  ensemble member:

  * ``ensemble.csv``: a file where the names and probabilities of the ensemble
    members are defined

  * ``forecast1``

    * the file ``timeseries_import.csv``
    * the file ``initial_state.csv``

  * ``forecast2``

    * ``timeseries_import.csv``
    * ``initial_state.csv``

  * ...

* ``output``: The folder where the output is saved:

  * ``forecast1``

    * ``timeseries_export.csv``

  * ``forecast2``

    * ``timeseries_export.csv``

  * ...

The Model
---------

.. note::

    This example uses the same hydraulic model as the basic example. For a
    detailed explanation of the hydraulic model, see :doc:`basic`.


In OpenModelica Connection Editor, the model looks like this:

.. image:: ../../images/simple_storage_openmodelica.png

In text mode, the Modelica model is as follows (with annotation statements
removed):

.. literalinclude:: ../../_build/mo/ensemble.mo
  :language: modelica
  :lineno-match:

The Optimization Problem
------------------------

The python script consists of the following blocks:

* Import of packages
* Declaration of Goals
* Declaration of the optimization problem class

  * Constructor
  * Set ``csv_ensemble_mode = True``
  * Declaration of a ``pre()`` method
  * Specification of Goals
  * Declaration of a ``priority_completed()`` method
  * Declaration of a ``post()`` method
  * Additional configuration of the solver

* A run statement

Importing Packages
''''''''''''''''''

For this example, the import block is as follows:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :lines: 1-10
  :lineno-match:

Declaring Goals
'''''''''''''''

First, we have a high priority goal to keep the water volume within a minimum
and maximum.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: WaterVolumeRangeGoal
  :lineno-match:

We also want to save energy, so we define a goal to minimize ``Q_release``. This
goal has a lower priority.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: MinimizeQreleaseGoal
  :lineno-match:

Optimization Problem
''''''''''''''''''''

Next, we construct the class by declaring it and inheriting the desired parent
classes.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example
  :lineno-match:
  :end-before: """

We turn on ensemble mode by setting ``csv_ensemble_mode = True``:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :lines: 49-50
  :lineno-match:

The method ``pre()`` is already defined in RTC-Tools, but we would like to add
a line to it to create a variable for storing intermediate results. To do
this, we declare a new ``pre()`` method, call ``super().pre()``
to ensure that the original method runs unmodified, and add in a variable
declaration to store our list of intermediate results. This variable is a
dict, reflecting the need to store results from multiple ensemble.

Because the timeseries we set will be the same for both ensemble members, we
also make sure that the timeseries we set are set for both ensemble members
using for loops.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.pre
  :lineno-match:

Now we pass in the goals:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.path_goals
  :lineno-match:

In order to better demonstrate the way that ensembles are handled in RTC-
Tools, we modify the ``control_tree_options()`` method. The default setting
allows the control tree to split at every time, but we override this method
and force it to split at a single timestep. See :ref:`ensemble-results` at
the bottom of the page for more information.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.control_tree_options
  :lineno-match:

We define the ``priority_completed()`` method. We ensure that it stores the
results from both ensemble members.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.priority_completed
  :lineno-match:

We output our intermediate results using the ``post()`` method:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.post
  :lineno-match:

Finally, we want to apply some additional configuration, reducing the amount of
information the solver outputs:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :pyobject: Example.solver_options
  :lineno-match:

Run the Optimization Problem
''''''''''''''''''''''''''''

To make our script run, at the bottom of our file we just have to call
the ``run_optimization_problem()`` method we imported on the optimization
problem class we just created.

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :lineno-match:
  :start-after: # Run

The Whole Script
''''''''''''''''

All together, the whole example script is as follows:

.. literalinclude:: ../../../examples/ensemble/src/example.py
  :language: python
  :lineno-match:

Running the Optimization Problem
--------------------------------

Following the execution of the optimization problem, the  ``post()`` method
should print out the following lines::

  Results for Ensemble Member 0:

  After finishing goals of priority 1:
  Level goal satisfied at 10 of 12 time steps
  Integral of Q_release = 17.34

  After finishing goals of priority 2:
  Level goal satisfied at 9 of 12 time steps
  Integral of Q_release = 17.12


  Results for Ensemble Member 1:

  After finishing goals of priority 1:
  Level goal satisfied at 10 of 12 time steps
  Integral of Q_release = 20.82

  After finishing goals of priority 2:
  Level goal satisfied at 9 of 12 time steps
  Integral of Q_release = 20.60


This is the same output as the output for :doc:`mixed_integer`, except
now the output for each ensemble is printed.


.. _ensemble-results:

Extracting Results
------------------

The results from the run are found in ``output/forecast1/timeseries_export.csv``
and ``output/forecast2/timeseries_export.csv``. Any CSV-reading software can
import it, but this is how results can be plotted using the python library
matplotlib: 

.. plot:: examples/pyplots/ensemble_results.py
   :include-source:

This plots the inflow and release values in two different ways: the middle graph 
depicts them in the same way you have seen until now (and this is how they truly 
should be interpreted). The lower plot shows the same points, but connected with 
line segments. This makes it easier to see where the flows diverge.   

Observations
------------

Note that in the results plotted above, the control tree follows a single path
and does not branch until it arrives at the first branching time. Up until the
branching point, RTC-Tools is making decisions that enhance the flexibility of
the system so that it can respond as ideally as possible to whichever future
emerges. In the case of two forecasts, this means taking a path that falls
between the two possible futures. This will cause the water level to diverge
from the ideal levels as time progresses. While this appears to be suboptimal,
it is preferable to simply gambling on one of the forecasts coming true and
ignoring the other. Once the branching time is reached, RTC-Tools is allowed
to optimize for each individual branch separately. Immediately, RTC-Tools
applies the corrective control needed to get the water levels into the
acceptable range. If the operator simply picks a forecast to use and guesses
wrong, the corrective control will have to be much more drastic and
potentially catastrophic.


