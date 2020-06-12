import unittest

from numpy.testing import assert_array_equal
import numpy as np

from seaice.sedna.cube import ConcentrationCube as Cube


ANYTHING = 9999.


class Test_mean_data_grid(unittest.TestCase):
    def test_mean_grid_with_grid_data_returns_same_grid(self):
        expected = np.ma.array([[36, 37], [100, 0]])
        cube = Cube(np.ma.array([[36, 37], [100, 0]]), missing_value=255.)

        actual = cube.mean_data_grid

        assert_array_equal(actual, expected)

    def test_mean_grid_with_cube_data_returns_grid_with_mean_grid_values(self):
        expected = np.ma.array([[74.5, 37.], [1.5, 3.]])

        grid1 = np.ma.array([[99., 37.], [1., 4.]])
        grid2 = np.ma.array([[50., 37.], [2., 2.]])

        cube = Cube(np.ma.dstack([grid1, grid2]), missing_value=255.)

        actual = cube.mean_data_grid

        assert_array_equal(actual, expected)


class Test__extent_binary_grid(unittest.TestCase):
    def test_with_grid_data(self):
        expected = np.ma.array([[0, 1], [1, 0]])
        cube = Cube(np.ma.array([[14, 37], [100, 0]]), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid(include_pole_hole=False)

        assert_array_equal(actual, expected)

    def test_with_grid_data_and_missing(self):
        expected = np.ma.array([[0, 1], [0, 0]])
        cube = Cube(np.ma.array([[14, 37], [255, 0]]), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid(include_pole_hole=False)

        assert_array_equal(actual, expected)

    def test_with_grid_data_and_mask(self):
        expected = np.ma.array([
            [0, 1],
            [1, 0]])
        data = np.ma.array([
            [251, 37],
            [100, 0]])
        cube = Cube(np.ma.masked_equal(data, 251), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid(include_pole_hole=False)

        assert_array_equal(actual, expected)

    def test_with_cube_data(self):
        expected = np.ma.array([[0, 1], [1, 0]])
        grid1 = np.ma.array([[16, 16], [100, 0]])
        grid2 = np.ma.array([[0, 14], [100, 0]])
        cube = Cube(np.ma.dstack([grid1, grid2]), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid(include_pole_hole=False)

        assert_array_equal(actual, expected)

    def test_with_cube_data_and_mask(self):
        expected = np.ma.array([[0, 1], [0, 1]])
        grid1 = np.ma.array([[16, 16], [100, 50]])
        grid2 = np.ma.array([[0., 14], [100, 50]])
        data = np.ma.dstack([grid1, grid2])
        cube = Cube(np.ma.masked_equal(data, 100), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid()

        assert_array_equal(actual, expected)
        assert_array_equal(actual.data, expected.data)

    def test_with_flag_value_and_grid_data(self):
        data = np.ma.masked_equal(np.ma.array([
            [251, 37],
            [251, 0]]), 251)

        cube = Cube(data, missing_value=255., extent_threshold=37)

        actual = cube._extent_binary_grid()

        expected = np.ma.array([
            [1, 1],
            [1, 0]])

        assert_array_equal(actual.data, expected.data)

    def test_with_flag_value_and_cube_data(self):
        grid1 = np.ma.array([
            [16., 16.],
            [100., 50.]])
        grid2 = np.ma.array([
            [100., 14.],
            [100., 50.]])

        data = np.ma.dstack([grid1, grid2])
        cube = Cube(np.ma.masked_equal(data, 100.), missing_value=255., extent_threshold=37,
                    flags={'pole': 100})

        actual = cube._extent_binary_grid()

        expected = np.ma.array([
            [0, 0],
            [1, 1]])

        assert_array_equal(actual.data, expected.data)

    def test_with_flag_value(self):
        grid1 = np.ma.masked_greater(np.ma.array([
            [1., 251., 255.],
            [0.,   6., 100.]]), 250)
        grid2 = np.ma.masked_greater(np.ma.array([
            [2.00, 251., 255.],
            [100.,   7., 100.]]), 250)
        grid3 = np.ma.masked_greater(np.ma.array([
            [100., 251., 255.],
            [79.0,   7., 100.]]), 250)
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid()

        expected = np.ma.array([
            [1, 1, 0],
            [1, 0, 1]])

        assert_array_equal(actual, expected)

    def test_with_no_mask_at_all(self):
        grid1 = np.ma.masked_greater(np.ma.array([
            [1., 95., 24.],
            [0.,   6., 100.]]), 250)
        grid2 = np.ma.masked_greater(np.ma.array([
            [2.00, 73., 24.],
            [100.,   7., 100.]]), 250)
        grid3 = np.ma.masked_greater(np.ma.array([
            [100., 83., 29.],
            [79.0,   7., 100.]]), 250)
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., extent_threshold=15,
                    flags={'pole': 251})

        actual = cube._extent_binary_grid(include_pole_hole=True)

        expected = np.ma.array([
            [1, 1, 1],
            [1, 0, 1]])

        assert_array_equal(actual, expected)

    def test_with_shrinking_pole_hole(self):
        grid1 = np.ma.masked_greater(np.ma.array([
            [251., 251., 251.],
            [0.,   6., 100.]]), 250)
        grid2 = np.ma.masked_greater(np.ma.array([
            [2.00, 251., 251.],
            [100.,   7., 100.]]), 250)
        grid3 = np.ma.masked_greater(np.ma.array([
            [100., 251., 251.],
            [79.0,   7., 100.]]), 250)
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., extent_threshold=15,
                    flags={'pole': 251})

        actual = cube._extent_binary_grid(include_pole_hole=True)

        expected = np.array([[1, 1, 1],
                             [1, 0, 1]])

        assert_array_equal(actual, expected)

    def test_with_shrinking_pole_hole_and_some_missing(self):
        grid1 = np.ma.masked_greater(np.ma.array([
            [251., 251., 251.],
            [0.,   6., 100.]]), 250)
        grid2 = np.ma.masked_greater(np.ma.array([
            [255, 251., 251.],
            [100.,   7., 100.]]), 250)
        grid3 = np.ma.masked_greater(np.ma.array([
            [16., 251., 251.],
            [79.0,   7., 100.]]), 250)
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., extent_threshold=15,
                    flags={'pole': 251})

        actual = cube._extent_binary_grid(include_pole_hole=True)

        expected = np.array([[1, 1, 1],
                             [1, 0, 1]])

        assert_array_equal(actual, expected)

    def test_with_shrinking_pole_hole_and_only_missing(self):
        grid1 = np.ma.masked_greater(np.ma.array([
            [251., 251., 251.],
            [0.,   6., 100.]]), 250)
        grid2 = np.ma.masked_greater(np.ma.array([
            [255, 251., 251.],
            [100.,   7., 100.]]), 250)
        grid3 = np.ma.masked_greater(np.ma.array([
            [255, 251., 251.],
            [79.0,   7., 100.]]), 250)
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., extent_threshold=15,
                    flags={'pole': 251})

        actual = cube._extent_binary_grid(include_pole_hole=True)

        expected = np.array([[0, 1, 1],
                             [1, 0, 1]])

        assert_array_equal(actual, expected)
        assert_array_equal(actual.data, expected.data)

    def test_concentration_values_below_threshold_are_zero_and_unmasked(self):
        expected = np.ma.array([[0, 0],
                                [0, 1]],
                               mask=[[False, True],
                                     [True, False]])

        cube = Cube(np.ma.array([[14, 255],
                                 [255, 50]]), missing_value=255., extent_threshold=15)

        actual = cube._extent_binary_grid(include_pole_hole=False)

        assert_array_equal(actual, expected)
        assert_array_equal(actual.data, expected.data)
        assert_array_equal(actual.mask, expected.mask)


class Test_extent(unittest.TestCase):
    def test_extent_with_grid_data(self):
        expected = 5 + 7
        cube = Cube(np.ma.array([[14, 16], [100, 0]]), missing_value=255.,
                    grid_areas=np.ma.array([[10, 5], [7, 1]]), extent_threshold=15)

        actual = cube.extent()

        self.assertEqual(actual, expected)

    def test_extent_with_cube_data(self):
        expected = 10 + 7

        grid1 = np.ma.array([[1., 4.], [0., 6.]])
        grid2 = np.ma.array([[2., 3.], [100., 7.]])
        grid3 = np.ma.array([[100., 5.], [79., 7.]])
        area_grid = np.ma.array([[10, 5], [7, 1]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15.)

        actual = cube.extent()

        self.assertEqual(actual, expected)

    def test_extent_with_masked_cube_data(self):
        expected = 10 + 7

        grid1 = np.ma.array([[1., 253.], [0., 6.]], mask=[[0, 1], [0, 0]])
        grid2 = np.ma.array([[2., 253.], [100., 7.]], mask=[[0, 1], [0, 0]])
        grid3 = np.ma.array([[100., 253.], [79., 7.]], mask=[[0, 1], [0, 0]])
        area_grid = np.ma.array([[10, 5], [7, 1]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15)

        actual = cube.extent()

        self.assertEqual(actual, expected)

    def test_extent_with_flag_value(self):
        expected = 10 + 7 + 5

        grid1 = np.ma.masked_equal(np.ma.array([
            [1., 251.],
            [0., 6.]]), 251)
        grid2 = np.ma.masked_equal(np.ma.array([
            [2., 251.],
            [100., 7.]]), 251)
        grid3 = np.ma.masked_equal(np.ma.array([
            [100., 251.],
            [79., 7.]]), 251)
        area_grid = np.ma.array([
            [10, 5],
            [7, 1]])

        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15)

        actual = cube.extent()

        self.assertEqual(actual, expected)

    def test_extent_with_pole_flag_value_and_missing_day(self):
        expected = 10 + 7

        grid1 = np.ma.masked_equal(np.ma.array([
            [1., 251.],
            [0., 6.]]), 251)
        grid2 = np.ma.masked_equal(np.ma.array([
            [255., 255.],
            [255., 255.]]), 255.)
        grid3 = np.ma.masked_equal(np.ma.array([
            [100., 251.],
            [79., 7.]]), 251)
        area_grid = np.ma.array([
            [10, 5],
            [7, 1]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15)

        actual = cube.extent()

        self.assertEqual(actual, expected)

    def test_extent_with_masked_region(self):
        cube = Cube(np.ma.array([[14, 16],
                                 [15, 0]]),
                    grid_areas=np.array([[10, 5],
                                         [7, 1]]))

        actual = cube.extent(regional_mask=[[True, True],
                                            [True, True]])

        self.assertTrue(np.isnan(actual))


class Test_missing(unittest.TestCase):
    def test_missing_with_grid_data(self):
        expected = 7

        cube = Cube(np.ma.array([[14, 16],
                                 [100, 0]]),
                    missing_value=100.,
                    grid_areas=np.array([[10, 5],
                                         [7, 1]]))

        actual = cube.missing()

        self.assertEqual(actual, expected)

    def test_missing_with_cube_data(self):
        expected = 10

        grid1 = np.ma.array([
            [255., 95.],
            [100., 100.]])
        grid2 = np.ma.array([
            [255., 90.],
            [100., 100.]])
        grid3 = np.ma.array([
            [255., 100.],
            [255., 100.]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255.,
                    grid_areas=np.ma.array([[10, 5],
                                            [7, 1]]))

        actual = cube.missing()

        self.assertEqual(actual, expected)

    def test_missing_with_masked_region(self):
        cube = Cube(np.ma.array([[14, 16],
                                 [15, 0]]),
                    missing_value=100.,
                    grid_areas=np.array([[10, 5],
                                         [7, 1]]))

        actual = cube.missing(regional_mask=[[True, True],
                                             [True, True]])

        self.assertTrue(np.isnan(actual))


class Test__missing_binary_grid(unittest.TestCase):
    def test__missing_binary_grid(self):
        expected = np.array([[False, False],
                             [True, False]])

        cube = Cube(np.ma.array([
            [14, 16],
            [100, 0]]), missing_value=100.)

        actual = cube._missing_binary_grid()

        assert_array_equal(actual, expected)

    def test__missing_binary_grid_with_cube_data(self):
        expected = np.array([[True, False],
                             [False, False]])

        grid1 = np.ma.array([
            [255., 95.],
            [100., 100.]])
        grid2 = np.ma.array([
            [255., 90.],
            [100., 100.]])
        grid3 = np.ma.array([
            [255., 100.],
            [255., 100.]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255.)

        actual = cube._missing_binary_grid()

        assert_array_equal(actual, expected)

    def test__missing_binary_grid_with_cube_data_and_some_missing_in_the_invalid_data_mask(self):
        expected = np.array([[True, False, False],
                             [False, False, False]])

        grid1 = np.ma.array([
            [255., 95., 255.],
            [100., 100., 10.]])
        grid2 = np.ma.array([
            [255., 90., 255.],
            [100., 100., 20.]])
        grid3 = np.ma.array([
            [255., 100., 255.],
            [255., 100., 30.]])
        invalid_data_mask = np.array([[False, False, True],
                                      [False, False, False]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255.,
                    invalid_data_mask=invalid_data_mask)

        actual = cube._missing_binary_grid()

        assert_array_equal(actual, expected)


class Test_area(unittest.TestCase):
    def test_area_with_grid_data(self):
        expected = ((5 * 16) + (7 * 100)) / 100.
        area_grid = np.ma.array([[10, 5], [7, 1]])
        cube = Cube(np.ma.array([[14, 16], [100, 0]]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15.)
        actual = cube.area()

        self.assertEqual(actual, expected)

    def test_area_with_grid_data_and_missing_data(self):
        expected = ((5 * 0) + (7 * 100)) / 100.
        area_grid = np.ma.array([[10, 5], [7, 1]])
        cube = Cube(np.ma.array([[14, 255], [100, 0]]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15.)
        actual = cube.area()

        self.assertEqual(actual, expected)

    def test_area_with_cube_data(self):
        expected = ((10 * (103. / 3.)) + (7 * (179. / 3))) / 100.

        grid1 = np.ma.array([[1., 4.], [0., 6.]])
        grid2 = np.ma.array([[2., 3.], [100., 7.]])
        grid3 = np.ma.array([[100., 5.], [79., 7.]])
        area_grid = np.ma.array([[10, 5], [7, 1]])
        cube = Cube(np.ma.dstack([grid1, grid2, grid3]), missing_value=255., grid_areas=area_grid,
                    extent_threshold=15.)
        actual = cube.area()

        self.assertEqual(actual, expected)

    def test_area_with_masked_region(self):
        cube = Cube(np.ma.array([[14, 16],
                                 [15, 0]]),
                    grid_areas=np.array([[10, 5],
                                         [7, 1]]))

        actual = cube.area(regional_mask=[[True, True],
                                          [True, True]])

        self.assertTrue(np.isnan(actual))


class Test__mask_invalid(unittest.TestCase):
    def test__mask_invalid(self):
        grid = np.ma.array([
            [1., 251.],
            [5., 6.]], mask=[
                [False, True],
                [False, False]])

        expected = np.ma.array([
            [np.nan, np.nan],
            [5., np.nan]])

        expected_mask = np.ma.array([
            [True, True],
            [False, True]])

        invalid_data = np.ma.array([
            [True, False],
            [False, True]])

        cube = Cube(np.array([[0., 0.], [0., 0.]]), invalid_data_mask=invalid_data)

        actual = cube._mask_invalid(grid)

        assert_array_equal(actual, expected)
        assert_array_equal(actual.mask, expected_mask)


class Test__invalid_data_mask(unittest.TestCase):

    def setUp(self):
        self.testcube = Cube(np.array([[10., 20., 30.],
                                       [50., 60., 90.]]))

    def test_with_wrong_shape(self):
        invalid_data_mask = np.array([True, False])
        self.assertRaises(ValueError, Cube._invalid_data_mask, self.testcube, invalid_data_mask)

    def test_with_None_arg_returns_all_false(self):
        expected = np.array([[False, False, False],
                             [False, False, False]])

        actual = Cube._invalid_data_mask(self.testcube, None)

        assert_array_equal(expected, actual)

    def test_with_correct_mask(self):
        mask = np.array([[False, True, False],
                         [False, False, False]])
        expected = mask.copy()

        actual = Cube._invalid_data_mask(self.testcube, mask)

        assert_array_equal(expected, actual)


class Test__grid_areas(unittest.TestCase):

    def setUp(self):
        self.testcube = Cube(np.array([[10., 20., 30.],
                                       [50., 60., 90.]]))

    def test_with_wrong_shape(self):
        grid_areas = np.array([2.5, 8])
        self.assertRaises(ValueError, Cube._grid_areas, self.testcube, grid_areas)

    def test_with_None_arg_returns_all_false(self):
        expected = np.array([[1.0, 1.0, 1.0],
                             [1.0, 1.0, 1.0]])

        actual = Cube._grid_areas(self.testcube, None)

        assert_array_equal(expected, actual)

    def test_with_correct_mask(self):
        mask = np.array([[1.0, 2.0, 7.0],
                         [8.0, 5.0, 3.0]])
        expected = mask.copy()

        actual = Cube._grid_areas(self.testcube, mask)

        assert_array_equal(expected, actual)


class Test__extent_grid(unittest.TestCase):
    def setUp(self):
        self.concentration = np.array([[1., 2.],
                                       [3., 4.]])

        self.grid_areas = np.array([[3., 4.],
                                    [5., 6.]])

    def test_extent_grid(self):
        cube = Cube(self.concentration, grid_areas=self.grid_areas)

        actual = cube._extent_grid()

        expected = np.array([[3, 4.],
                             [5, 6.]])

        assert_array_equal(actual, expected)

    def test_concentration_below_threshold(self):
        cube = Cube(self.concentration, grid_areas=self.grid_areas, extent_threshold=2)

        actual = cube._extent_grid()

        expected = np.array([[0, 4.],
                             [5, 6.]])

        assert_array_equal(actual, expected)


class Test__area_grid(unittest.TestCase):
    def setUp(self):
        self.concentration = np.array([[50., 75.],
                                       [80., 100.]])

        self.grid_areas = np.array([[4., 4.],
                                    [5., 6.]])

    def test_area_grid(self):
        cube = Cube(self.concentration, grid_areas=self.grid_areas)

        actual = cube._area_grid()

        expected = np.array([[2., 3],
                             [4., 6]])

        assert_array_equal(actual, expected)

    def test_concentration_below_threshold(self):
        cube = Cube(self.concentration, grid_areas=self.grid_areas, extent_threshold=51)

        actual = cube._area_grid()

        expected = np.array([[0, 3.],
                             [4, 6.]])

        assert_array_equal(actual, expected)


class Test__missing_grid(unittest.TestCase):
    def setUp(self):
        self.concentration = np.array([[1., 2.],
                                       [3., 3.]])

        self.grid_areas = np.array([[3., 4.],
                                    [5., 6.]])

        self.missing_value = 3

        self.regional_mask = np.array([[False, True],
                                       [False, True]])

    def test_basic_missing(self):
        cube = Cube(self.concentration, grid_areas=self.grid_areas,
                    missing_value=self.missing_value)

        actual = cube._missing_grid()

        expected = np.ma.array([[0, 0],
                                [5, 6]],
                               mask=[[False, False],
                                     [False, False]])

        assert_array_equal(actual, expected)
        assert_array_equal(actual.mask, expected.mask)


class Test_grid_shape(unittest.TestCase):
    def test_with_3d_data(self):
        layer1 = np.array([[1., 2., 3., 4.],
                           [3., 3., 5., 6.],
                           [3., 3., 5., 6.]])
        layer2 = np.array([[2., 3., 1., 4.],
                           [3., 5., 3., 6.],
                           [3., 3., 6., 5.]])

        cube = Cube(np.ma.dstack([layer1, layer2]))

        actual = cube.grid_shape()
        expected = (3, 4)

        self.assertTupleEqual(actual, expected)

    def test_with_2d_data(self):
        cube = Cube(np.array([[1., 2., 3.],
                              [3., 3., 5.],
                              [5., 3., 3.],
                              [3., 5., 3.]]))

        actual = cube.grid_shape()
        expected = (4, 3)

        self.assertTupleEqual(actual, expected)
