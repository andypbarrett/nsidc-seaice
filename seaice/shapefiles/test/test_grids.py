import unittest

import numpy as np
import numpy.testing as npt

from seaice.shapefiles.grids import _massage_grid
from seaice.shapefiles.grids import _data_massage_land_like


class Test__data_massage_land_like(unittest.TestCase):
    land = 1
    land_like = [2, 3, 4]

    def test_replaces_land_like_with_land(self):
        data = np.array([[1, 2, 3, 4, 5, 0],
                         [1, 2, 3, 4, 5, 0]])

        actual = _data_massage_land_like(data, self.land, self.land_like)

        expected = np.array([[1, 1, 1, 1, 5, 0],
                             [1, 1, 1, 1, 5, 0]])

        npt.assert_array_equal(expected, actual)

    def test_returns_unmodified_arary_when_no_land_like(self):
        data = np.array([[1, 20, 30, 40, 5, 0],
                         [1, 20, 30, 40, 5, 0]])

        actual = _data_massage_land_like(data, self.land, self.land_like)

        expected = np.array([[1, 20, 30, 40, 5, 0],
                             [1, 20, 30, 40, 5, 0]])

        npt.assert_array_equal(expected, actual)


class Test__massage_grid(unittest.TestCase):
    def test_returns_grid_when_no_options_given(self):
        grid = np.array([[1, 0],
                         [1, 0]])

        actual = _massage_grid(grid)

        expected = grid

        npt.assert_array_equal(expected, actual)

    def test_keep_flag_values_converts_non_1_vals_to_0(self):
        grid = np.array([[1, 55],
                         [1, 0]])

        actual = _massage_grid(grid, keep_flag_values=False)

        expected = np.array([[1, 0],
                             [1, 0]])

        npt.assert_array_equal(expected, actual)
