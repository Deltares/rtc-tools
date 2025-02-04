import unittest

import numpy as np

from rtctools.optimization.optimization_problem import OptimizationProblem
from rtctools.optimization.timeseries import Timeseries


class TestMergeBounds(unittest.TestCase):
    def test_merge_equal_types(self):
        m, M = OptimizationProblem.merge_bounds((1, 3), (2, 4))
        self.assertEqual(m, 2)
        self.assertEqual(M, 3)

        m, M = OptimizationProblem.merge_bounds(
            (np.array([2, 1, 0.5]), 3), (np.array([1, 2, 0.0]), 4)
        )

        self.assertTrue(np.array_equal(m, np.array([2, 2, 0.5])))
        self.assertEqual(M, 3)

        m, M = OptimizationProblem.merge_bounds(
            (1, Timeseries([1, 2, 3], [1, 4, 1])), (2, Timeseries([1, 2, 3], [1.5, 2, 3]))
        )

        self.assertEqual(m, 2)
        self.assertTrue(np.array_equal(M.times, np.array([1, 2, 3])))
        self.assertTrue(np.array_equal(M.values, np.array([1, 2, 1])))

    def test_simple_merge_with_upcast(self):
        m, M = OptimizationProblem.merge_bounds((2, 3), (Timeseries([1, 2, 3], [1, 4, 1]), 4))
        self.assertTrue(np.array_equal(m.values, np.array([2, 4, 2])))
        self.assertEqual(M, 3)

        m, M = OptimizationProblem.merge_bounds((2, 3), (np.array([1, 4, 1]), 4))
        self.assertTrue(np.array_equal(m, np.array([2, 4, 2])))
        self.assertEqual(M, 3)

    def test_checks_and_exceptions(self):
        # Timeseries times/values lengths are not equal
        with self.assertRaisesRegex(Exception, "different lengths"):
            m, M = OptimizationProblem.merge_bounds(
                (1, Timeseries([1, 2, 3], [1, 4, 1])), (2, Timeseries([2, 3], [2, 3]))
            )

        # Timeseries times are not equal
        with self.assertRaisesRegex(Exception, "non-equal times"):
            m, M = OptimizationProblem.merge_bounds(
                (1, Timeseries([1, 2, 3], [1, 4, 1])), (2, Timeseries([2, 3, 4], [2, 3, 1]))
            )

        # Mismatching vector sizes
        with self.assertRaisesRegex(Exception, "non-equal size"):
            m, M = OptimizationProblem.merge_bounds(
                (np.array([2, 1, 0.5]), 2), (np.array([1, 2]), 4)
            )

        # 1D Timeseries merge with 2D Timeseries
        with self.assertRaisesRegex(Exception, "non-equal size"):
            m, M = OptimizationProblem.merge_bounds(
                (1, Timeseries([1, 2, 3], [1, 4, 1])),
                (2, Timeseries([1, 2, 3], [[2, 3, 1], [2, 3, 1]])),
            )

        # 2D Timeseries merge with differently shaped other 2D Timeseries
        with self.assertRaisesRegex(Exception, "non-equal size"):
            m, M = OptimizationProblem.merge_bounds(
                (1, Timeseries([1, 2, 3], [[1, 4, 1], [1, 4, 1]])),
                (2, Timeseries([1, 2, 3], [[2, 3, 1], [2, 3, 1], [2, 3, 1]])),
            )
        # Vector with 2D Timeseries mismatch
        with self.assertRaisesRegex(Exception, "vector size when upcasting"):
            m, M = OptimizationProblem.merge_bounds(
                (np.array([2, 1, 3]), 2), (Timeseries([1, 2, 3], [[1, 4], [1.5, 2], [0, 0]]), 4)
            )

    def test_upcast_2d(self):
        m, M = OptimizationProblem.merge_bounds(
            (np.array([2, 1]), 2), (Timeseries([1, 2, 3], [[1, 4], [1.5, 2], [0, 0]]), 4)
        )
        self.assertTrue(np.array_equal(m.values, np.array([[2, 4], [2, 2], [2, 1]])))

    def test_upcast_single_element_vector_as_float(self):
        m, M = OptimizationProblem.merge_bounds(
            (np.array([2]), 2), (Timeseries([1, 2, 3], [[1, 4], [1.5, 2], [0, 0]]), 4)
        )
        self.assertTrue(np.array_equal(m.values, np.array([[2, 4], [2, 2], [2, 2]])))
