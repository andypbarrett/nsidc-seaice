import datetime as dt
import itertools
import re
import unittest
from unittest.mock import patch

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt

import seaice.data.trend as trend
from .util import mock_today
import seaice.nasateam as nt


class Test__daily_std_gridset_for_trends(unittest.TestCase):

    minimum_days = 20
    insufficient_days = 19

    @patch('seaice.data.getter.double_weight_smmr_files')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.trend._std_gridset')
    def test_gets_std_gridset_for_each_year(self, mock_std_gridset,
                                            mock_all_daily_file_paths_for_month,
                                            mock_double_weight_smmr_files):
        nt_hemi = {'short_name': 'N'},
        year = 1981
        month = 1
        search_paths = ['/file/system/']

        mock_std_gridset.return_value = {'data': np.array([[4., 4.],
                                                           [4., 4.]]),
                                         'metadata': {'files': [],
                                                      'period_index': pd.PeriodIndex([], freq='D')}}

        mock_all_daily_file_paths_for_month.return_value = [''] * self.minimum_days
        mock_double_weight_smmr_files.return_value = [''] * self.minimum_days

        actual = trend._daily_std_gridset_for_trends(nt_hemi, year, month, search_paths)

        self.assertEqual(mock_std_gridset.call_args_list[0][0][0], nt_hemi)
        pdt.assert_index_equal(mock_std_gridset.call_args_list[0][0][1],
                               pd.date_range(start='1979-01-01', end='1979-01-31'))
        mock_all_daily_file_paths_for_month.assert_any_call(nt_hemi, 1979, 1, search_paths)

        self.assertEqual(mock_std_gridset.call_args_list[1][0][0], nt_hemi)
        pdt.assert_index_equal(mock_std_gridset.call_args_list[1][0][1],
                               pd.date_range(start='1980-01-01', end='1980-01-31'))
        mock_all_daily_file_paths_for_month.assert_any_call(nt_hemi, 1980, 1, search_paths)

        self.assertEqual(mock_std_gridset.call_args_list[2][0][0], nt_hemi)
        pdt.assert_index_equal(mock_std_gridset.call_args_list[2][0][1],
                               pd.date_range(start='1981-01-01', end='1981-01-31'))
        mock_all_daily_file_paths_for_month.assert_any_call(nt_hemi, 1981, 1, search_paths)

        npt.assert_array_equal(actual['data'], np.full((2, 2, 3), 4.))

    @patch('seaice.data.getter.double_weight_smmr_files')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.trend._std_gridset')
    def test_uses_nans_for_year_with_insufficient_files(self, mock_std_gridset,
                                                        mock_all_daily_file_paths_for_month,
                                                        mock_double_weight_smmr_files):
        nt_hemi = {'short_name': 'N', 'shape': (2, 2)}
        year = 1981
        month = 1
        search_paths = ['/file/system/']

        mock_std_gridset.return_value = {'data': np.array([[4., 4.],
                                                           [4., 4.]]),
                                         'metadata': {'files': [],
                                                      'period_index': pd.PeriodIndex([], freq='D')}}

        mock_all_daily_file_paths_for_month.side_effect = [[''] * self.minimum_days,
                                                           [''] * self.insufficient_days,
                                                           [''] * self.minimum_days]
        mock_double_weight_smmr_files.side_effect = [[''] * self.minimum_days,
                                                     [''] * self.insufficient_days,
                                                     [''] * self.minimum_days]

        actual = trend._daily_std_gridset_for_trends(nt_hemi, year, month, search_paths)

        expected = np.dstack([
            np.array([[4., 4.],
                      [4., 4.]]),
            np.array([[np.nan, np.nan],
                      [np.nan, np.nan]]),
            np.array([[4., 4.],
                      [4., 4.]])
        ])

        npt.assert_array_equal(actual['data'], expected)


class Test__daily_std_gridset_for_seasonal_trends(unittest.TestCase):
    @patch('seaice.data.trend._std_gridset')
    def test_calls_std_gridsets_with_seasonal_dates_for_each_year(self, _mock_std_gridset):
        nt_hemi = nt.NORTH
        year = 2000
        months = (3, 4, 5)
        search_paths = ['wherever']
        min_days_for_valid_month = 20

        trend._daily_std_gridset_for_seasonal_trends(
            nt_hemi, year, months, search_paths, min_days_for_valid_month
        )

        call_args_list = trend._std_gridset.call_args_list
        years = range(1979, year + 1)

        # each call should have a date index matching the year after the
        # previous call; unittest's assert_any_call doesn't work here since we
        # need to compare pandas DatetimeIndex objects, so loop and use pdt
        # instead
        for (args, _kwargs), y in zip(call_args_list, years):
            self.assertEqual(args[0], nt.NORTH)

            expected_date_index = pd.date_range(
                start=dt.date(y, 3, 1),
                end=dt.date(y, 5, 31),
                freq='D'
            )
            pdt.assert_index_equal(args[1], expected_date_index)

    @patch('seaice.data.trend._std_gridset')
    def test_groupby_calls_std_gridsets_with_correct_seasonal_dates_for_custom_winter(
            self,
            _mock_std_gridset
    ):
        nt_hemi = nt.NORTH
        year = 1981

        # use custom winter ending in january so that the end date is always the
        # 31st
        months = (11, 12, 1)
        search_paths = ['wherever']
        min_days_for_valid_month = 20

        trend._daily_std_gridset_for_seasonal_trends(
            nt_hemi, year, months, search_paths, min_days_for_valid_month
        )

        call_args_list = trend._std_gridset.call_args_list
        years = range(1979, year + 1)

        # each call should have a date index matching the year after the
        # previous call; unittest's assert_any_call doesn't work here since we
        # need to compare pandas DatetimeIndex objects, so loop and use pdt
        # instead
        for (args, _kwargs), y in zip(call_args_list, years):
            self.assertEqual(args[0], nt.NORTH)

            expected_date_index = pd.date_range(
                start=dt.date(y - 1, 11, 1),
                end=dt.date(y, 1, 31),
                freq='D'
            )
            pdt.assert_index_equal(args[1], expected_date_index)

    @patch('seaice.data.trend._std_gridset')
    def test_stacks_data_from_std_gridsets_calls(self, _mock_std_gridset):
        nt_hemi = nt.NORTH
        year = 1981
        months = (3, 4, 5)
        search_paths = ['wherever']
        min_days_for_valid_month = 20

        grid0 = np.array([[0, 0],
                          [3, 3]])
        grid1 = np.array([[1, 1],
                          [4, 4]])
        grid2 = np.array([[2, 2],
                          [5, 5]])

        trend._std_gridset.side_effect = [
            {
                'data': grid0,
                'metadata': {'files': [], 'period_index': []}
            },
            {
                'data': grid1,
                'metadata': {'files': [], 'period_index': []}
            },
            {
                'data': grid2,
                'metadata': {'files': [], 'period_index': []}
            }
        ]

        actual = trend._daily_std_gridset_for_seasonal_trends(
            nt_hemi, year, months, search_paths, min_days_for_valid_month
        )

        expected_data = np.dstack([grid0, grid1, grid2])

        npt.assert_array_equal(actual['data'], expected_data)

    @patch('seaice.data.trend._std_gridset')
    def test_metadata(self, _mock_std_gridset):
        nt_hemi = nt.NORTH
        year = 1981
        months = (3, 4, 5)
        search_paths = ['wherever']
        min_days_for_valid_month = 20

        the_grid = np.array([])

        trend._std_gridset.side_effect = [
            {
                'data': the_grid,
                'metadata': {'files': ['daily_files_1981'],
                             'period_index': ['period_index_1981']}
            },
            {
                'data': the_grid,
                'metadata': {'files': ['daily_files_1982'],
                             'period_index': ['period_index_1982']}
            },
            {
                'data': the_grid,
                'metadata': {'files': ['daily_files_1983'],
                             'period_index': ['period_index_1983']}
            }
        ]

        actual = trend._daily_std_gridset_for_seasonal_trends(
            nt_hemi, year, months, search_paths, min_days_for_valid_month
        )

        expected_metadata = {
            'files': [
                ['daily_files_1981'],
                ['daily_files_1982'],
                ['daily_files_1983']
            ],
            'period_indexes': [
                ['period_index_1981'],
                ['period_index_1982'],
                ['period_index_1983']
            ]
        }

        self.assertEqual(actual['metadata'], expected_metadata)


class Test__datetime_index_for_trends(unittest.TestCase):
    def test_starts_on_the_first_of_a_month(self):
        actual_index = trend._datetime_index_for_trends(2015, 12)
        actual = actual_index[0].day

        expected = 1

        self.assertEqual(actual, expected)

    def test_default_starts_within_the_satellite_era(self):
        actual_index = trend._datetime_index_for_trends(2015, 12)
        actual = actual_index[0].date()

        self.assertGreaterEqual(actual, nt.BEGINNING_OF_SATELLITE_ERA)

    def test_default_starts_near_the_beginning_of_satellite_era(self):
        actual_index = trend._datetime_index_for_trends(2015, 12)
        actual = actual_index[0].date()

        latest_start = nt.BEGINNING_OF_SATELLITE_ERA + dt.timedelta(365)

        self.assertGreaterEqual(latest_start, actual)

    def test_only_has_days_for_given_month(self):
        actual_index = trend._datetime_index_for_trends(2015, 12)
        actual = np.unique(actual_index.month)

        expected = np.array([12])

        npt.assert_array_equal(actual, expected)

    def test_only_goes_up_to_given_year(self):
        actual_index = trend._datetime_index_for_trends(2012, 12)
        actual = actual_index.year.max()

        expected = 2012

        self.assertEqual(actual, expected)

    @mock_today(2013, 10, 28)
    def test_only_goes_up_to_previous_year_if_given_yearmonth_is_incomplete(self):
        actual_index = trend._datetime_index_for_trends(2013, 10)
        actual = actual_index.year.max()

        expected = 2012

        self.assertEqual(actual, expected)

    @mock_today(2013, 10, 28)
    def test_only_goes_up_to_current_year_when_given_future_yearmonth(self):
        actual_index = trend._datetime_index_for_trends(2014, 9)
        actual = actual_index.year.max()

        expected = 2013

        self.assertEqual(actual, expected)

    def test_starts_at_given_start_year(self):
        actual_index = trend._datetime_index_for_trends(2010, 10, start_year=2009)
        actual = actual_index[0].year

        expected = 2009

        self.assertEqual(actual, expected)

    def test_starts_at_beginning_of_sat_era_when_start_year_before_beginning(self):
        """Tests that the datetime index starts at the beginning of the
        satellite era when the given start year is before then.
        """
        actual_index = trend._datetime_index_for_trends(2010, 12, start_year=1000)
        actual = actual_index[0].year

        expected = nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY.year

        self.assertEqual(actual, expected)


class Test__gridset_matches_platform(unittest.TestCase):
    def test_returns_true_for_matching_platform_pattern(self):
        gridset = {'metadata': {'files': ['file_abc.bin']}}
        pattern = re.compile('file_(?P<platform>.*).bin')
        platform = 'abc'

        actual = trend._gridset_matches_platform(gridset, pattern, platform)

        self.assertTrue(actual)

    def test_returns_false_for_matching_platform_pattern(self):
        gridset = {'metadata': {'files': ['file_abc.bin']}}
        pattern = re.compile('file_(?P<platform>.*).bin')
        platform = 'def'

        actual = trend._gridset_matches_platform(gridset, pattern, platform)

        self.assertFalse(actual)


class Test__std_gridset(unittest.TestCase):

    @patch('seaice.data.api.concentration_daily')
    def test_gets_concentration_for_each_day_in_given_datetime_index(self,
                                                                     mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1980-01-01', end='1980-01-31')

        mock_concentration_daily.return_value = {'data': np.array([[0., 0.], [0., 0.]]),
                                                 'metadata': {
                                                     'files': [],
                                                     'period_index': pd.PeriodIndex([], freq='D'),
                                                     'valid_data_range': (0, 100)
                                                 }}

        actual = trend._std_gridset(nt_hemi, dates)

        npt.assert_array_equal(actual['data'], np.zeros((2, 2)))

        self.assertEqual(len(mock_concentration_daily.mock_calls), 31)

    @patch('seaice.data.api.concentration_daily')
    def test_gets_standard_deviation_for_each_point(self, mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1980-01-01', end='1980-01-03')

        mock_concentration_daily.side_effect = [
            {'data': np.array([[1., 2.],
                               [3., 4.]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[2, 4],
                               [6, 8]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[3, 6],
                               [9, 12]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }}
        ]

        actual = trend._std_gridset(nt_hemi, dates)

        expected = np.array([[np.array([1, 2, 3]).std(), np.array([2, 4, 6]).std()],
                             [np.array([3, 6, 9]).std(), np.array([4, 8, 12]).std()]])

        npt.assert_array_equal(actual['data'], expected)

    @patch('seaice.data.api.concentration_daily')
    def test_skips_empty_gridsets(self, mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1980-01-01', end='1980-01-03')

        mock_concentration_daily.side_effect = [
            {'data': np.array([[1., 2.],
                               [3., 4.]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[99, 99],
                               [99, 99]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100),
                 'empty_gridset': True
             }},
            {'data': np.array([[3, 6],
                               [9, 12]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }}
        ]

        actual = trend._std_gridset(nt_hemi, dates)

        expected = np.array([[np.array([1, 3]).std(), np.array([2, 6]).std()],
                             [np.array([3, 9]).std(), np.array([4, 12]).std()]])

        npt.assert_array_equal(actual['data'], expected)

    @patch('seaice.data.api.concentration_daily')
    def test_skips_values_outside_valid_range(self, mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1980-01-01', end='1980-01-03')

        mock_concentration_daily.side_effect = [
            {'data': np.array([[1., 2.],
                               [3., 4.]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 20)
             }},
            {'data': np.array([[21, 21],
                               [21, 21]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 20)
             }},
            {'data': np.array([[3, 6],
                               [9, 12]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 20)
             }}
        ]

        actual = trend._std_gridset(nt_hemi, dates)

        expected = np.array([[np.array([1, 3]).std(), np.array([2, 6]).std()],
                             [np.array([3, 9]).std(), np.array([4, 12]).std()]])

        npt.assert_array_equal(actual['data'], expected)

    @patch('seaice.data.api.concentration_daily')
    def test_points_with_all_invalid_values_set_to_zero(self, mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1980-01-01', end='1980-01-03')

        mock_concentration_daily.side_effect = [
            {'data': np.array([[101., 2.],
                               [3., 4.]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[101, 4],
                               [6, 8]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[101, 6],
                               [9, 12]]),
             'metadata': {
                 'files': [],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }}
        ]

        actual = trend._std_gridset(nt_hemi, dates)

        expected = np.array([[0,                         np.array([2, 4, 6]).std()],
                             [np.array([3, 6, 9]).std(), np.array([4, 8, 12]).std()]])

        npt.assert_array_equal(actual['data'], expected)

    @patch('seaice.data.api.concentration_daily')
    def test_double_weights_smmr_files(self, mock_concentration_daily):
        nt_hemi = {}
        dates = pd.date_range(start='1987-08-20', end='1987-08-21')

        mock_concentration_daily.side_effect = [
            {'data': np.array([[15., 15.],
                               [15., 15.]]),
             'metadata': {
                 'files': ['nt_19870820_n07_v1.1_n.bin'],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }},
            {'data': np.array([[20, 20],
                               [20, 20]]),
             'metadata': {
                 'files': ['nt_19870821_f08_v1.1_n.bin'],
                 'period_index': pd.PeriodIndex([], freq='D'),
                 'valid_data_range': (0, 100)
             }}
        ]

        actual_gridset = trend._std_gridset(nt_hemi, dates)
        actual_data = actual_gridset['data']
        actual_files = actual_gridset['metadata']['files']

        expected_files = [['nt_19870820_n07_v1.1_n.bin'],
                          ['nt_19870820_n07_v1.1_n.bin'],
                          ['nt_19870821_f08_v1.1_n.bin']]
        expected_std = np.array([15, 15, 20]).std()
        expected_data = np.full((2, 2), expected_std)

        npt.assert_array_equal(actual_data, expected_data)
        self.assertEqual(actual_files, expected_files)


class Test__trend_grid(unittest.TestCase):
    def test_returns_zero_with_zero_weights(self):
        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[2., 2.],
                          [2., 2.]])
        conc3 = np.array([[3., 3.],
                          [3., 3.]])
        concentration_cube = np.dstack([conc1, conc2, conc3])

        weight_cube = np.zeros_like(concentration_cube)

        actual = trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        expected = np.zeros((2, 2))

        npt.assert_array_equal(actual, expected)

    def test_returns_slopes_with_one_weight(self):
        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[2., 3.],
                          [4., 5.]])
        conc3 = np.array([[3., 5.],
                          [7., 9.]])
        concentration_cube = np.dstack([conc1, conc2, conc3])

        weight_cube = np.ones_like(concentration_cube)

        actual = trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        expected = np.array([[10., 20.],
                             [30., 40.]])

        npt.assert_array_almost_equal(actual, expected)

    def test_points_with_high_uncertainty_set_to_zero(self):
        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[2., 3.],
                          [4., 5.]])
        conc3 = np.array([[3., 5.],
                          [7777., 9.]])
        concentration_cube = np.dstack([conc1, conc2, conc3])

        weight_cube = np.ones_like(concentration_cube)

        actual = trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        expected = np.array([[10., 20.],
                             [0., 40.]])

        npt.assert_array_almost_equal(actual, expected)

    def test_skips_layers_with_zero_weight(self):
        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[2., 3.],
                          [4., 5.]])
        conc3 = np.array([[3333, 5555],
                          [7777, 9999]])
        conc4 = np.array([[4., 7.],
                          [10., 13.]])
        concentration_cube = np.dstack([conc1, conc2, conc3, conc4])

        weight0 = np.zeros_like(conc1)
        weight1 = np.ones_like(conc1)
        weight_cube = np.dstack([weight1, weight1, weight0, weight1])

        actual = trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        expected = np.array([[10., 20.],
                             [30., 40.]])

        npt.assert_array_almost_equal(actual, expected)

    def test_points_with_fewer_than_three_nonzero_weighted_values_set_to_zero(self):
        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[2., 3.],
                          [4., 5.]])
        conc3 = np.array([[3., 5.],
                          [7., 9.]])
        concentration_cube = np.dstack([conc1, conc2, conc3])

        weight1 = np.ones_like(conc1)
        weight = np.array([[1., 1.],
                           [0., 1.]])
        weight_cube = np.dstack([weight1, weight1, weight])

        actual = trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        expected = np.array([[10., 20.],
                             [0., 40.]])

        npt.assert_array_almost_equal(actual, expected)

    def test_requires_concentration_and_weight_to_have_same_shape(self):
        concentration_cube = np.full((2, 2, 3), 5, dtype=np.int)
        weight_cube = np.full((2, 2, 4), 6, dtype=np.int)
        with self.assertRaises(AssertionError):
            trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

    # test that we pass the weights on, but don't worry about testing how they
    # affect the resulting numbers
    @patch('seaice.data.trend.ThreadPool')
    @patch('statsmodels.api.WLS')
    def test_weights_passed_to_regression_function(self, mock_WLS, mock_pool):
        class mock_WLS_value(object):
            class result(object):
                f_pvalue = .01
                params = [np.nan, 5]

            def fit(self):
                return self.result()

        class mock_pool_value(object):
            def __enter__(self, *args):
                return self

            def __exit__(self, *args):
                pass

            def starmap(self, f, arr):
                return list(itertools.starmap(f, arr))

        mock_WLS.return_value = mock_WLS_value()
        mock_pool.return_value = mock_pool_value()

        conc1 = np.array([[1., 1.],
                          [1., 1.]])
        conc2 = np.array([[1., 3.],
                          [4., 5.]])
        conc3 = np.array([[3., 5.],
                          [7., 9.]])
        concentration_cube = np.dstack([conc1, conc2, conc3])

        weight1 = np.array([[.19, .17],
                            [.19, .17]])
        weight2 = np.array([[0.5, 0.5],
                            [0.5, 0.5]])
        weight3 = np.array([[0.33, 0.25],
                            [0.33, 0.25]])
        weight_cube = np.dstack([weight1, weight2, weight3])

        trend._trend_grid(concentration_cube, weight_cube, clipping_threshold=100)

        # http://connor-johnson.com/2014/02/18/linear-regression-with-python/
        #
        # See trend.py where statsmodels.add_constant is called
        X = np.stack([np.array([1, 1, 1]), np.array([0, 1, 2])], axis=1)

        npt.assert_array_equal(mock_WLS.call_args_list[0][0][0], np.array([1, 1, 3]))
        npt.assert_array_equal(mock_WLS.call_args_list[0][0][1], X)
        npt.assert_array_equal(mock_WLS.call_args_list[0][1]['weights'], np.array([.19, 0.5, 0.33]))

        npt.assert_array_equal(mock_WLS.call_args_list[1][0][0], np.array([1, 3, 5]))
        npt.assert_array_equal(mock_WLS.call_args_list[1][0][1], X)
        npt.assert_array_equal(mock_WLS.call_args_list[1][1]['weights'], np.array([.17, 0.5, 0.25]))

        npt.assert_array_equal(mock_WLS.call_args_list[2][0][0], np.array([1, 4, 7]))
        npt.assert_array_equal(mock_WLS.call_args_list[2][0][1], X)
        npt.assert_array_equal(mock_WLS.call_args_list[2][1]['weights'], np.array([.19, 0.5, 0.33]))

        npt.assert_array_equal(mock_WLS.call_args_list[3][0][0], np.array([1, 5, 9]))
        npt.assert_array_equal(mock_WLS.call_args_list[3][0][1], X)
        npt.assert_array_equal(mock_WLS.call_args_list[3][1]['weights'], np.array([.17, 0.5, 0.25]))


class Test__weight_from_std(unittest.TestCase):
    def test_returns_one_over_std_squared(self):
        std = np.array([[1/1., 1/2.],
                        [1/3., 1/4.]])

        actual = trend._weight_from_std(std)

        expected = np.array([[1., 4.],
                             [9., 16.]])

        npt.assert_array_equal(actual, expected)

    def test_returns_zero_when_std_is_zero(self):
        std = np.array([[0., 1/2.],
                        [1/3., 0.]])

        actual = trend._weight_from_std(std)

        expected = np.array([[0., 4.],
                             [9., 0.]])

        npt.assert_array_equal(actual, expected)

    def test_returns_zero_when_std_is_NaN(self):
        std = np.array([[np.nan, 1/2.],
                        [1/3., np.nan]])

        actual = trend._weight_from_std(std)

        expected = np.array([[0., 4.],
                             [9., 0.]])

        npt.assert_array_equal(actual, expected)
