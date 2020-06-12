import unittest

import numpy as np
import numpy.testing as npt

from seaice.shapefiles.geom import _feature_grid


class Test__feature_grid(unittest.TestCase):
    def test_returns_1s_in_cells_matching_the_value(self):
        grid = np.array([[1, 2],
                         [4, 5]])

        value = 5

        actual = _feature_grid(grid, value)

        expected = np.array([[0, 0],
                             [0, 1]])

        npt.assert_array_equal(expected, actual)

    def test_returns_1s_in_cells_matching_multiple_values(self):
        grid = np.array([[1, 2],
                         [4, 5]])

        values = [4, 5]

        actual = _feature_grid(grid, *values)

        expected = np.array([[0, 0],
                             [1, 1]])

        npt.assert_array_equal(expected, actual)
