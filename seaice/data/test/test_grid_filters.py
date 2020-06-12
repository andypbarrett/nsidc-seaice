import functools
import unittest

import numpy as np
import numpy.testing as npt

import seaice.data.grid_filters as grid_filters
from seaice.data.errors import SeaIceDataTypeError


class Test_concentration_cutoff(unittest.TestCase):
    concentration_cutoff = functools.partial(grid_filters.concentration_cutoff, 15)

    def test_with_nothing_to_cutoff(self):
        grid = np.array([[15, 16],
                         [15, 10293120]])

        actual = self.concentration_cutoff(grid)

        expected = np.array([[15, 16],
                             [15, 10293120]])

        npt.assert_array_equal(actual, expected)

    def test_converts_values_below_cutoff_to_zero(self):
        grid = np.array([[15, 16],
                         [15, 14]])

        actual = self.concentration_cutoff(grid)

        expected = np.array([[15, 16],
                             [15, 0]])

        npt.assert_array_equal(actual, expected)

    def test_with_masked_data(self):
        grid = np.ma.array([[50, 10],
                            [7, 20]],
                           mask=[[False, True],
                                 [False, True]])

        actual = self.concentration_cutoff(grid)

        expected = np.ma.array([[50, 10],
                                [0, 20]],
                               mask=[[False, True],
                                     [False, True]])

        npt.assert_array_equal(actual.data, expected.data)
        npt.assert_array_equal(actual.mask, expected.mask)

    def test_raises_error_if_not_numpy_array(self):
        grid = [[15, 16],
                [15, 14]]

        with self.assertRaises(SeaIceDataTypeError):
            self.concentration_cutoff(grid)
