import unittest

import numpy as np
import numpy.testing as npt

import seaice.data.cube as c


class Test_average_cube(unittest.TestCase):
    def test_averages_each_layer(self):
        d1 = np.array([[5., 5.],
                       [10., 10.]]).astype(np.float)
        d2 = np.array([[7., 7.],
                       [12., 12.]]).astype(np.float)
        cube = np.dstack((d1, d2))

        actual = c.average_cube(cube)

        expected = np.array([[6., 6.],
                             [11., 11.]]).astype(np.float)

        npt.assert_array_equal(expected, actual)

    def test_averages_unmasked_values(self):
        d1 = np.array([[5., 5.],
                       [10., 10.]]).astype(np.float)
        d1 = np.ma.masked_equal(d1, 5.)

        d2 = np.array([[7., 8.],
                       [12., 8.]]).astype(np.float)
        d2 = np.ma.masked_equal(d2, 8.)

        cube = np.ma.dstack((d1, d2))

        expected = np.ma.array([[7., 0],
                                [11., 10.]],
                               mask=[[False, True],
                                     [False, False]]).astype(np.float)

        actual = c.average_cube(cube)

        npt.assert_array_equal(expected.data, actual.data)
        npt.assert_array_equal(expected.mask, actual.mask)


class Test_apply_patch(unittest.TestCase):
    def test_patches_masked_data(self):
        d1 = np.array([[5., 5., 5.],
                       [9., 9., 9.],
                       [10., 10., 10.]]).astype(np.float)
        d1 = np.ma.masked_equal(d1, 5.)

        patch = np.array([[1., 2., 3.],
                          [99., 99., 99.],
                          [100., 100., 100.]]).astype(np.float)

        expected = np.ma.array([[1., 2., 3.],
                                [9., 9., 9.],
                                [10., 10., 10.]]).astype(np.float)

        actual = c.apply_patch(d1, patch)
        npt.assert_array_equal(expected, actual)

    def test_returns_grid_when_no_masked_data_to_patch(self):
        d1 = np.ma.array([[5., 5., 5.],
                          [9., 9., 9.],
                          [10., 10., 10.]]).astype(np.float)

        patch = np.array([[1., 2., 3.],
                          [99., 99., 99.],
                          [100., 100., 100.]]).astype(np.float)

        expected = np.ma.array([[5., 5., 5.],
                                [9., 9., 9.],
                                [10., 10., 10.]]).astype(np.float)

        actual = c.apply_patch(d1, patch)
        npt.assert_array_equal(expected, actual)
