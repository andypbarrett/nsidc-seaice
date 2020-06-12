import datetime as dt
import unittest
from unittest.mock import patch

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt

import seaice.data.gridset_filters as gf
from seaice.data.gridset_filters import apply_largest_pole_hole
from seaice.data.gridset_filters import concentration_cutoff
from seaice.data.gridset_filters import drop_invalid_ice
from seaice.data.gridset_filters import drop_bad_dates
from seaice.data.gridset_filters import drop_land
from seaice.data.gridset_filters import prevent_empty
from seaice.data.gridset_filters import ensure_full_nrt_month
import seaice.data.errors as e
import seaice.nasateam as nt

LAND = nt.FLAGS['land']
COAST = nt.FLAGS['coast']


class Test_apply_largest_pole_hole(unittest.TestCase):
    def test_no_pole_hole(self):
        gridset = {'data': np.array([[1, 1],
                                     [1, 1]]),
                   'metadata': {'flags': {'pole': 251},
                                'missing_value': 255}}

        actual = apply_largest_pole_hole(gridset)

        npt.assert_array_equal(gridset['data'], actual['data'])

    def test_one_pole_hole(self):
        layer1 = np.array([[251, 1],
                           [1, 1]])
        layer2 = np.array([[2, 2],
                           [2, 2]])

        gridset = {'data': np.dstack([layer1, layer2]),
                   'metadata': {'flags': {'pole': 251},
                                'missing_value': 255}}

        actual = apply_largest_pole_hole(gridset)

        expected_layer2 = np.array([[251, 2],
                                    [2, 2]])
        expected = np.dstack([layer1, expected_layer2])

        npt.assert_array_equal(expected, actual['data'])

    def test_different_pole_holes(self):
        layer1 = np.array([[251, 1],
                           [1, 1]])
        layer2 = np.array([[251, 251],
                           [2, 2]])

        gridset = {'data': np.dstack([layer1, layer2]),
                   'metadata': {'flags': {'pole': 251},
                                'missing_value': 255}}

        actual = apply_largest_pole_hole(gridset)

        expected_layer1 = np.array([[251, 251],
                                    [1, 1]])
        expected_layer2 = np.array([[251, 251],
                                    [2, 2]])
        expected = np.dstack([expected_layer1, expected_layer2])

        npt.assert_array_equal(expected, actual['data'])

    def test_with_layer_of_all_missing(self):
        layer1 = np.array([[251, 1],
                           [1, 1]])
        layer2 = np.array([[251, 251],
                           [2, 2]])
        layer3 = np.array([[255, 255],
                           [255, 255]])

        gridset = {'data': np.dstack([layer1, layer2, layer3]),
                   'metadata': {'flags': {'pole': 251},
                                'missing_value': 255}}

        actual = apply_largest_pole_hole(gridset)

        expected_layer1 = np.array([[251, 251],
                                    [1, 1]])
        expected_layer2 = np.array([[251, 251],
                                    [2, 2]])
        expected_layer3 = np.array([[255, 255],
                                    [255, 255]])
        expected = np.dstack([expected_layer1, expected_layer2, expected_layer3])

        npt.assert_array_equal(expected, actual['data'])


class Test_concentration_cutoff(unittest.TestCase):
    @patch('seaice.data.grid_filters.concentration_cutoff')
    def test_calls_grid_filters_concentration_cutoff(self, mock_concentration_cutoff):
        gridset = {
            'data': np.array([[20, 10],
                              [5, 50]])
        }
        mock_concentration_cutoff.return_value = np.array([[20, 0],
                                                           [0, 50]])

        expected = {
            'data': np.array([[20, 0],
                              [0, 50]])
        }

        actual = concentration_cutoff(15, gridset)

        npt.assert_array_equal(expected['data'], actual['data'])

        self.assertEqual(15, mock_concentration_cutoff.call_args[0][0])
        npt.assert_array_equal(np.array([[20, 10],
                                         [5, 50]]), mock_concentration_cutoff.call_args[0][1])


class Test_drop_bad_dates(unittest.TestCase):
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_no_bad_data(self,
                         mock_get_bad_days_for_hemisphere):
        gridset = {
            'data': np.full((5, 5, 3), 10, dtype=np.int),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '2.bin', '3.bin'],
                'period_index': pd.period_range('2016-01-01', '2016-01-03', freq='D')
            }
        }
        bad_dates_index = pd.PeriodIndex([], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['1.bin', '2.bin', '3.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.period_range('2016-01-01', '2016-01-03', freq='D'))
        npt.assert_array_equal(actual['data'],
                               np.full((5, 5, 3), 10, dtype=np.int))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_all_bad_data(self,
                          mock_get_bad_days_for_hemisphere):

        the_period_index = pd.period_range('2016-01-01', '2016-01-03', freq='D')
        gridset = {
            'data': np.full((5, 5, 3), 10, dtype=np.int),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '2.bin', '3.bin'],
                'period_index': the_period_index,
                'period': pd.Period(dt.date(2016, 2, 2), freq='D'),
                'missing_value': 255
            }
        }

        bad_dates_index = the_period_index.copy()
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         [])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex([], dtype='period[D]'))
        npt.assert_array_equal(actual['data'], np.full((5, 5), 255, dtype=np.int))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_middle_day_bad(self,
                            mock_get_bad_days_for_hemisphere):
        zeroth_grid = np.full((5, 5), 0, dtype=np.int)
        first_grid = np.full((5, 5), 1, dtype=np.int)
        second_grid = np.full((5, 5), 2, dtype=np.int)

        gridset = {
            'data': np.dstack([zeroth_grid, first_grid, second_grid]),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '2.bin', '3.bin'],
                'period_index': pd.period_range('2016-01-01', '2016-01-03', freq='D')
            }
        }
        bad_dates_index = pd.PeriodIndex(['2016-01-02'], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['1.bin', '3.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2016-01-01', '2016-01-03'], freq='D'))
        npt.assert_array_equal(actual['data'], np.dstack([zeroth_grid, second_grid]))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_two_days_bad(self,
                          mock_get_bad_days_for_hemisphere):
        zeroth_grid = np.full((5, 5), 0, dtype=np.int)
        first_grid = np.full((5, 5), 1, dtype=np.int)
        second_grid = np.full((5, 5), 2, dtype=np.int)

        gridset = {
            'data': np.dstack([zeroth_grid, first_grid, second_grid]),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '2.bin', '3.bin'],
                'period_index': pd.period_range('2016-01-01', '2016-01-03', freq='D')
            }
        }

        bad_dates_index = pd.PeriodIndex(['2016-01-02', '2016-01-03'], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['1.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2016-01-01'], freq='D'))
        npt.assert_array_equal(actual['data'], zeroth_grid)

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_no_bad_data_double_weighted_dates(self,
                                               mock_get_bad_days_for_hemisphere):
        gridset = {
            'data': np.full((5, 5, 3), 10, dtype=np.int),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '1.bin', '2.bin'],
                'period_index': pd.PeriodIndex(['2016-01-01', '2016-01-01', '2016-01-02'], freq='D')
            }
        }
        bad_dates_index = pd.PeriodIndex([], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['1.bin', '1.bin', '2.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2016-01-01', '2016-01-01', '2016-01-02'], freq='D'))
        npt.assert_array_equal(actual['data'],
                               np.full((5, 5, 3), 10, dtype=np.int))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_all_bad_data_double_weighted_dates(self,
                                                mock_get_bad_days_for_hemisphere):

        the_period_index = pd.PeriodIndex(['2016-01-01', '2016-01-01', '2016-01-02'], freq='D')
        gridset = {
            'data': np.full((5, 5, 3), 10, dtype=np.int),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '1.bin', '2.bin'],
                'period_index': the_period_index,
                'period': pd.Period(dt.date(2016, 2, 2), freq='D'),
                'missing_value': 255
            }
        }

        bad_dates_index = the_period_index.copy()
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         [])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex([], dtype='period[D]'))
        npt.assert_array_equal(actual['data'], np.full((5, 5), 255, dtype=np.int))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_day_bad_double_weighted_dates(self,
                                           mock_get_bad_days_for_hemisphere):
        zeroth_grid = np.full((5, 5), 0, dtype=np.int)
        first_grid = np.full((5, 5), 1, dtype=np.int)
        second_grid = np.full((5, 5), 2, dtype=np.int)

        gridset = {
            'data': np.dstack([zeroth_grid, zeroth_grid, first_grid, second_grid]),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '1.bin', '2.bin', '3.bin'],
                'period_index': pd.PeriodIndex(['2016-01-01',
                                                '2016-01-01',
                                                '2016-01-02',
                                                '2016-01-03'], freq='D')
            }
        }
        bad_dates_index = pd.PeriodIndex(['2016-01-02'], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['1.bin', '1.bin', '3.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2016-01-01', '2016-01-01', '2016-01-03'], freq='D'))
        npt.assert_array_equal(actual['data'], np.dstack([zeroth_grid, zeroth_grid, second_grid]))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_double_weighted_day_bad_double_weighted_dates(self,
                                                           mock_get_bad_days_for_hemisphere):
        zeroth_grid = np.full((5, 5), 0, dtype=np.int)
        first_grid = np.full((5, 5), 1, dtype=np.int)
        second_grid = np.full((5, 5), 2, dtype=np.int)

        gridset = {
            'data': np.dstack([zeroth_grid, zeroth_grid, first_grid, second_grid]),
            'metadata': {
                'hemi': 'N',
                'temporality': 'D',
                'files': ['1.bin', '1.bin', '2.bin', '3.bin'],
                'period_index': pd.PeriodIndex(['2016-01-01',
                                                '2016-01-01',
                                                '2016-01-02',
                                                '2016-01-03'], freq='D')
            }
        }

        bad_dates_index = pd.PeriodIndex(['2016-01-01', '2016-01-02'], freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates_index

        actual = drop_bad_dates(gridset)

        self.assertEqual(actual['metadata']['files'],
                         ['3.bin'])
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2016-01-03'], freq='D'))
        npt.assert_array_equal(actual['data'], second_grid)


class Test_drop_invalid_ice(unittest.TestCase):

    def test_preserves_flag_and_removes_invalid_ice(self):
        invalid_ice_mask = np.array([[False, False],
                                     [False, True]])

        gridset = {
            'data': np.array([[100, 251],
                              [100, 100]]),
            'metadata': {'valid_data_range': (0, 100), 'missing_value': 255}
        }

        actual = drop_invalid_ice(invalid_ice_mask, gridset)

        expected_data = np.array([[100, 251],
                                  [100, 0]])

        self.assertTrue(actual['metadata']['drop_invalid_ice'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_preserves_flag_where_invalid_mask_is_present(self):
        invalid_ice_mask = np.array([[False, True],
                                     [False, True]])

        gridset = {
            'data': np.array([[100, 251],
                              [100, 100]]),
            'metadata': {'valid_data_range': (0, 100), 'missing_value': 255}
        }

        actual = drop_invalid_ice(invalid_ice_mask, gridset)

        expected_data = np.array([[100, 251],
                                  [100, 0]])

        self.assertTrue(actual['metadata']['drop_invalid_ice'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_does_nothing_when_no_invalid_ice(self):
        invalid_ice_mask = np.array([[False, False],
                                     [False, False]])

        gridset = {
            'data': np.array([[100, 251],
                              [100, 100]]),
            'metadata': {'valid_data_range': (0, 100), 'missing_value': 255}
        }

        actual = drop_invalid_ice(invalid_ice_mask, gridset)

        expected_data = np.array([[100, 251],
                                  [100, 100]])

        self.assertTrue(actual['metadata']['drop_invalid_ice'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_removes_missing_in_invalid_regions_and_leaves_it_in_valid_ones(self):
        invalid_ice_mask = np.array([[True, False],
                                     [True, False],
                                     [True, False]])

        gridset = {
            'data': np.array([[100, 251],
                              [100, 100],
                              [255, 255]]),
            'metadata': {'valid_data_range': (0, 100),
                         'missing_value': 255}
        }

        actual = drop_invalid_ice(invalid_ice_mask, gridset)

        expected_data = np.array([[0, 251],
                                  [0, 100],
                                  [0, 255]])

        self.assertTrue(actual['metadata']['drop_invalid_ice'])
        npt.assert_array_equal(expected_data, actual['data'])

    def test_leaves_all_missing_alone(self):
        invalid_ice_mask = np.array([[True, False],
                                     [True, False],
                                     [True, False]])

        gridset = {
            'data': np.array([[255, 255],
                              [255, 255],
                              [255, 255]]),
            'metadata': {'valid_data_range': (0, 100),
                         'missing_value': 255}
        }

        actual = drop_invalid_ice(invalid_ice_mask, gridset)

        expected_data = np.array([[255, 255],
                                  [255, 255],
                                  [255, 255]])

        self.assertNotIn('drop_invalid_ice', actual['metadata'])
        npt.assert_array_equal(expected_data, actual['data'])


class Test_drop_land(unittest.TestCase):
    def test_drops_land_values(self):
        gridset = {
            'data': np.array([[100, LAND],
                              [100, 100]]),
            'metadata': {}
        }

        actual = drop_land(LAND, COAST, gridset)

        expected_data = np.array([[100, 0],
                                  [100, 100]])

        self.assertTrue(actual['metadata']['drop_land'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_drops_coast_values(self):
        gridset = {
            'data': np.array([[100, 100],
                              [100, COAST]]),
            'metadata': {}
        }

        actual = drop_land(LAND, COAST, gridset)

        expected_data = np.array([[100, 100],
                                  [100, 0]])

        self.assertTrue(actual['metadata']['drop_land'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_drops_land_and_coast_values(self):
        gridset = {
            'data': np.array([[100, LAND],
                              [100, COAST]]),
            'metadata': {}
        }

        actual = drop_land(LAND, COAST, gridset)

        expected_data = np.array([[100, 0],
                                  [100, 0]])

        self.assertTrue(actual['metadata']['drop_land'])
        npt.assert_array_equal(actual['data'], expected_data)

    def test_does_nothing_when_no_land(self):
        gridset = {
            'data': np.array([[100, 76],
                              [100, 100]]),
            'metadata': {}
        }

        actual = drop_land(LAND, COAST, gridset)

        expected_data = np.array([[100, 76],
                                  [100, 100]])

        self.assertTrue(actual['metadata']['drop_land'])
        npt.assert_array_equal(actual['data'], expected_data)


class Test_ensure_full_nrt_monthly(unittest.TestCase):

    def setUp(self):
        self.gridset = {
            'data': 'NA for this test',
            'metadata': {
                'files': [None] * 31,
                'period_index': pd.period_range('1/1/2001', '1/31/2001', freq='D'),
                'period': pd.Period('2001-01', freq='M'),
                'temporality': 'M'
            }
        }

    def test_returns_exception_when_period_index_is_daily_and_nrt_filelist_is_incomplete(self):
        self.gridset['metadata']['files'] = [None] * 20
        with self.assertRaises(e.IncompleteNRTGridsetError):
            ensure_full_nrt_month(self.gridset)

    def test_returns_gridset_when_period_index_is_daily_and_nrt_filelist_is_complete(self):
        actual = ensure_full_nrt_month(self.gridset)
        expected = self.gridset

        self.assertEqual(actual, expected)

    def test_returns_gridset_when_temporality_is_incorrect(self):
        self.gridset['metadata']['temporality'] = 'D'
        expected = self.gridset
        actual = ensure_full_nrt_month(self.gridset)

        self.assertEqual(actual, expected)

    def test_returns_gridset_when_period_is_monthly(self):
        self.gridset['metadata']['files'] = [None]
        self.gridset['metadata']['period_index'] = pd.period_range('1/1/2001', '1/1/2001', freq='M')
        self.gridset['metadata']['period'] = pd.Period('2001-01', freq='M')

        expected = self.gridset
        actual = ensure_full_nrt_month(self.gridset)

        self.assertEqual(actual, expected)


class Test_prevent_empty(unittest.TestCase):
    def test_returns_same_nonempty_gridset(self):
        gridset = {
            'data': np.array([[100, 76],
                              [255, 100]]),
            'metadata': {'missing_value': 255}
        }

        actual = prevent_empty(gridset)

        expected_data = np.array([[100, 76],
                                  [255, 100]])

        self.assertEqual(actual['metadata'], {'missing_value': 255})
        npt.assert_array_equal(actual['data'], expected_data)

    def test_raises_error_with_all_missing_gridset(self):
        gridset = {
            'data': np.array([[255, 255],
                              [255, 255]]),
            'metadata': {'missing_value': 255}
        }

        with self.assertRaises(e.SeaIceDataNoData):
            prevent_empty(gridset)


class Test__interpolate_missing(unittest.TestCase):
    def test_when_no_missing_data(self):
        data_grid = np.ma.array([[50., 50.],
                                 [100., 100.]])

        zeros = np.zeros_like(data_grid)
        interpolation_grids = np.expand_dims(zeros, axis=2)

        # expected is just the data grid when there's no missing data
        expected = data_grid

        actual = gf._interpolate_missing(data_grid, interpolation_grids)

        npt.assert_array_equal(expected.data, actual.data)

    def test_when_data_is_masked(self):

        missing = 255

        data_grid = np.ma.array([[50., missing],
                                 [100., 100.]])
        zeros = np.zeros_like(data_grid)
        interpolation_grids = np.expand_dims(zeros, axis=2)

        data_grid = np.ma.masked_equal(data_grid, missing)

        expected = np.ma.array([[50., 0],
                                [100., 100.]])

        actual = gf._interpolate_missing(data_grid, interpolation_grids, missing_value=missing)

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.data, actual.data)

    def test_when_target_grid_is_all_missing(self):
        data_grid = np.ma.array([[50., 50.],
                                 [100., 100.]])
        zeros = np.zeros_like(data_grid)

        interpolation_grids = np.dstack([data_grid, zeros])

        target_grid = np.full(data_grid.shape, 255, dtype=np.int)

        expected = np.ma.array([[25., 25.],
                                [50., 50.]])

        actual = gf._interpolate_missing(target_grid, interpolation_grids)

        npt.assert_array_equal(expected.data, actual.data)

    def test_masked_flagged_values_unchanged_and_masked_no_missing(self):
        data_grid = np.array([[50., 251.],
                              [100., 253.]])

        interpolation_grids = np.expand_dims(data_grid.copy(), axis=2)

        expected = np.array([[50., 251.],
                             [100., 253.]])

        actual = gf._interpolate_missing(data_grid, interpolation_grids)

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.data, actual.data)

    def test_flagged_values_unchanged_with_missing(self):
        data_grid = np.ma.array([[50., 251.],
                                 [255., 253.]])

        data_grid2 = np.ma.array([[50., 251.],
                                  [75., 253.]])

        interpolation_grids = np.expand_dims(data_grid2, axis=2)

        expected = np.ma.array([[50., 251.],
                                [75., 253.]])

        actual = gf._interpolate_missing(data_grid, interpolation_grids)

        npt.assert_array_equal(expected, actual)

    def test_flagged_values_are_minimum_anded_with_missing(self):
        """Test pole hole is replaced by data if it shrinks or grows"""

        data_grid = np.ma.array([[50., 251.],
                                 [255., 253.]])

        data_grid2 = np.ma.array([[251., 251.],   # extra pole in this data
                                  [75., 253.]])

        interpolation_grids = np.dstack([data_grid, data_grid2])

        target_grid = np.full(data_grid.shape, 255, dtype=np.int)

        expected = np.ma.array([[50., 251.],   # extra pole is replaced
                                [75., 253.]])  # with data from data_grid

        actual = gf._interpolate_missing(target_grid, interpolation_grids)

        npt.assert_array_equal(expected, actual)

    def test_flagged_values_and_missing_mixed_together_return_missing(self):

        data_grid = np.ma.array([[255., 251.],
                                 [255., 253.]])

        data_grid2 = np.ma.array([[251., 251.],   # extra pole in this data
                                  [75., 253.]])

        target_grid = np.full(data_grid.shape, 255, dtype=np.int)
        interpolation_grids = np.dstack([data_grid, data_grid2])

        expected = np.ma.array([[255., 251.],
                                [75., 253.]])

        actual = gf._interpolate_missing(target_grid, interpolation_grids)

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.data, actual.data)

    def test_flagged_values_and_missing_and_data_mixed_together_return_data(self):

        data_grid = np.ma.array([[255., 251.],
                                 [255., 253.]])

        data_grid2 = np.ma.array([[251., 251.],   # extra pole in this data
                                  [75., 253.]])

        data_grid3 = np.ma.array([[50., 251.],
                                  [255., 253.]])

        interpolation_grids = np.dstack([data_grid, data_grid3])
        target_grid = data_grid2

        expected = np.ma.array([[50., 251.],
                                [75., 253.]])

        actual = gf._interpolate_missing(target_grid, interpolation_grids)

        npt.assert_array_equal(expected, actual)

    def test_with_missing_values(self):
        data_grid = np.array([[55., 0.],
                              [55., 53.]])

        data_grid2 = np.array([[60., 255.],
                               [75., 23.]])

        data_grid3 = np.array([[50., 100.],
                               [55., 53.]])

        interpolation_grids = np.dstack([data_grid, data_grid3])
        target_grid = data_grid2

        actual = gf._interpolate_missing(target_grid, interpolation_grids)

        expected_data = np.array([[60., 50.],
                                  [75., 23.]])

        npt.assert_array_equal(expected_data, actual)


class Test__index_by_date(unittest.TestCase):

    def test__index_by_date(self):
        filelist = ['nt_20120918_f17_v1.1_s.bin',
                    'nt_20120919_f13_v1.1_s.bin',
                    'nt_20120920_f17_v1.1_s.bin']
        date_ = dt.date(2012, 9, 19)
        expected = 1
        actual = gf._index_by_date(filelist, date_)
        self.assertEquals(expected, actual)

    def test__index_by_date_with_no_matches(self):
        filelist = ['nt_20120918_f17_v1.1_s.bin',
                    'nt_20120919_f13_v1.1_s.bin',
                    'nt_20120920_f17_v1.1_s.bin']
        date = dt.date(2014, 9, 19)

        with self.assertRaises(e.IndexNotFoundError):
            gf._index_by_date(filelist, date)


class Test__extent_grid_from_conc_grid(unittest.TestCase):
    def test_base_case(self):
        conc = np.array([[100, 100],
                         [100, 100]])

        actual = gf._extent_grid_from_conc_grid(conc)

        expected = np.array([[1, 1],
                             [1, 1]])

        npt.assert_array_equal(actual, expected)

    def test_default_valid_range(self):
        conc = np.array([[15, 100],
                         [14, 100]])

        actual = gf._extent_grid_from_conc_grid(conc)

        expected = np.array([[1, 1],
                             [0, 1]])

        npt.assert_array_equal(actual, expected)

    def test_only_counts_conc_within_range(self):
        conc = np.array([[50, 51],
                         [27, 26]])

        actual = gf._extent_grid_from_conc_grid(conc, valid_extent_range=(27, 50))

        expected = np.array([[1, 0],
                             [1, 0]])

        npt.assert_array_equal(actual, expected)

    def test_preserves_flag_values(self):
        conc = np.array([[100, 1977],
                         [100, 100]])

        flags = {
            'starwars': 1977
        }

        actual = gf._extent_grid_from_conc_grid(conc, flags=flags)

        expected = np.array([[1, 1977],
                             [1, 1]])

        npt.assert_array_equal(actual, expected)

    def test_counts_pole_flag_as_extent(self):
        conc = np.array([[100, 1977],
                         [100, 100]])

        flags = {
            'pole': 1977
        }

        actual = gf._extent_grid_from_conc_grid(conc, flags=flags)

        expected = np.array([[1, 1],
                             [1, 1]])

        npt.assert_array_equal(actual, expected)

    def test_all_the_options(self):
        conc = np.array([[13, 75, 100],
                         [12, 1977, 100],
                         [2389, 50, 100]])

        flags = {
            'pole': 1977,
            'special': 2389
        }

        actual = gf._extent_grid_from_conc_grid(conc,
                                                valid_extent_range=(13, 99),
                                                flags=flags)

        expected = np.array([[1, 1, 0],
                             [0, 1, 0],
                             [2389, 1, 0]])

        npt.assert_array_equal(actual, expected)

    def test_empty_gridset(self):
        conc = np.array([[255, 255],
                         [255, 255]])

        flags = {
            'missing': 255
        }

        actual = gf._extent_grid_from_conc_grid(conc, flags=flags)

        expected = np.array([[255, 255],
                             [255, 255]])

        npt.assert_array_equal(actual, expected)
