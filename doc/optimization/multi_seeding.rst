Using multiple seeds
====================

A seed can be defined by implementing the :py:meth:`OptimizationProblem.seed` method.
To implement a workflow for solving an optimization problem by trying multiple seeds,
one can use the :py:class:`MultiSeedMixin` class.

.. autoclass:: rtctools.optimization.multi_seed_mixin.MultiSeedMixin
    :members: use_seed_id, selected_seed_id, seed_ids, seed_from_id
    :show-inheritance:
