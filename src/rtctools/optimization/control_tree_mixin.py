import logging
from typing import Dict, List, Tuple, Union

import numpy as np

from .optimization_problem import OptimizationProblem

logger = logging.getLogger("rtctools")


class ControlTreeMixin(OptimizationProblem):
    """
    Adds a stochastic control tree to your optimization problem.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__branches = {}

    def control_tree_options(self) -> Dict[str, Union[List[str], List[float], int]]:
        """
        Returns a dictionary of options controlling the creation of a k-ary stochastic tree.

        +------------------------+---------------------+-----------------------+
        | Option                 | Type                | Default value         |
        +========================+=====================+=======================+
        | ``forecast_variables`` | ``list`` of strings | All constant inputs   |
        +------------------------+---------------------+-----------------------+
        | ``branching_times``    | ``list`` of floats  | ``self.times()``      |
        +------------------------+---------------------+-----------------------+
        | ``k``                  | ``int``             | ``2``                 |
        +------------------------+---------------------+-----------------------+

        A ``k``-ary tree is generated, branching at every interior branching time.
        Ensemble members are clustered to paths through the tree based on average
        distance over all forecast variables.

        :returns: A dictionary of control tree generation options.
        """

        options = {}

        options["forecast_variables"] = [
            var.name() for var in self.dae_variables["constant_inputs"]
        ]
        options["branching_times"] = self.times()[1:]
        options["k"] = 2

        return options

    def discretize_control(self, variable, ensemble_member, times, offset):
        control_indices = np.zeros(len(times), dtype=np.int16)
        for branch, members in self.__branches.items():
            if ensemble_member not in members:
                continue

            branching_time_0 = self.__branching_times[len(branch) + 0]
            branching_time_1 = self.__branching_times[len(branch) + 1]
            els = np.logical_and(times >= branching_time_0, times < branching_time_1)
            nnz = np.count_nonzero(els)
            try:
                control_indices[els] = self.__discretize_controls_cache[(variable, branch)]
            except KeyError:
                control_indices[els] = list(range(offset, offset + nnz))
                self.__discretize_controls_cache[(variable, branch)] = control_indices[els]
                offset += nnz
        return control_indices

    def discretize_controls(self, resolved_bounds):
        self.__discretize_controls_cache = {}

        # Collect options
        options = self.control_tree_options()

        # Make sure branching times contain initial and final time.  The
        # presence of these is assumed below.
        times = self.times()
        t0 = self.initial_time
        self.__branching_times = options["branching_times"]
        n_branching_times = len(self.__branching_times)
        if n_branching_times > len(times) - 1:
            raise Exception("Too many branching points specified")
        self.__branching_times = np.concatenate(([t0], self.__branching_times, [np.inf]))

        logger.debug("ControlTreeMixin: Branching times:")
        logger.debug(self.__branching_times)

        # Avoid calling constant_inputs() many times
        constant_inputs = [
            self.constant_inputs(ensemble_member=i) for i in range(self.ensemble_size)
        ]

        # Branches start at branching times, so that the tree looks like the following:
        #
        #         *-----
        #   *-----
        #         *-----
        #
        #   t0    t1
        #
        # with branching time t1.
        branches = {}

        def branch(current_branch: Tuple[int]):
            if len(current_branch) >= n_branching_times:
                return

            # Branch stats
            n_branch_members = len(branches[current_branch])
            if n_branch_members == 0:
                # Nothing to do
                return
            distances = np.zeros((n_branch_members, n_branch_members))

            # Decide branching on a segment of the time horizon
            branching_time_0 = self.__branching_times[len(current_branch) + 1]
            branching_time_1 = self.__branching_times[len(current_branch) + 2]

            # Compute reverse ensemble member index-to-distance index map.
            reverse = {}
            for i, member_i in enumerate(branches[current_branch]):
                reverse[member_i] = i

            # Compute distances between ensemble members, summed for all
            # forecast variables
            for forecast_variable in options["forecast_variables"]:
                # We assume the time stamps of the forecasts in all ensemble
                # members to be identical
                timeseries = constant_inputs[0][forecast_variable]
                els = np.logical_and(
                    timeseries.times >= branching_time_0, timeseries.times < branching_time_1
                )

                # Compute distance between ensemble members
                for i, member_i in enumerate(branches[current_branch]):
                    timeseries_i = constant_inputs[member_i][forecast_variable]
                    for j, member_j in enumerate(branches[current_branch]):
                        timeseries_j = constant_inputs[member_j][forecast_variable]
                        distances[i, j] += np.linalg.norm(
                            timeseries_i.values[els] - timeseries_j.values[els]
                        )

            # Keep track of ensemble members that have not yet been allocated
            # to a new branch
            available = set(branches[current_branch])

            # Special case: if k >= len(available), assign one ensemble member to each branch
            if options["k"] >= len(available):
                available_list = list(available)
                for i in range(options["k"]):
                    if i < len(available_list):
                        branches[current_branch + (i,)] = [available_list[i]]
                    else:
                        branches[current_branch + (i,)] = []
            else:
                # Standard branching logic
                # We first select the scenario with the max distance to any other branch
                idx = np.argmax(np.amax(distances, axis=0))

                for i in range(options["k"]):
                    if idx >= 0:
                        branches[current_branch + (i,)] = [branches[current_branch][idx]]

                        available.remove(branches[current_branch][idx])

                        # We select the scenario with the max min distance to the other branches
                        min_distances = np.array(
                            [
                                min(
                                    [np.inf]
                                    + [
                                        distances[j, k]
                                        for j, member_j in enumerate(branches[current_branch])
                                        if member_j not in available and member_k in available
                                    ]
                                )
                                for k, member_k in enumerate(branches[current_branch])
                            ],
                            dtype=np.float64,
                        )
                        min_distances[np.where(min_distances == np.inf)] = -np.inf

                        idx = np.argmax(min_distances)
                        if min_distances[idx] <= 0:
                            idx = -1
                    else:
                        branches[current_branch + (i,)] = []

                # Cluster remaining ensemble members to branches
                for member_i in available:
                    min_i = 0
                    min_distance = np.inf
                    for i in range(options["k"]):
                        branch2 = branches[current_branch + (i,)]
                        if len(branch2) > 0:
                            distance = distances[reverse[member_i], reverse[branch2[0]]]
                            if distance < min_distance:
                                min_distance = distance
                                min_i = i
                    branches[current_branch + (min_i,)].append(member_i)

            # Recurse
            for i in range(options["k"]):
                branch(current_branch + (i,))

        current_branch = ()
        branches[current_branch] = list(range(self.ensemble_size))
        branch(current_branch)

        logger.debug("ControlTreeMixin:  Control tree is:")
        logger.debug(branches)

        self.__branches = branches

        # By now, the tree branches have been set up.  We now rely
        # on the default discretization logic to call discretize_control()
        # for each (control variable, ensemble member) pair.
        return super().discretize_controls(resolved_bounds)

    @property
    def control_tree_branches(self) -> Dict[Tuple[int], List[int]]:
        """
        Returns a dictionary mapping the branch id (a Tuple of ints) to a list
        of ensemble members in said branch.

        Note that the root branch is an empty tuple containing all ensemble
        members.
        """

        return self.__branches.copy()
