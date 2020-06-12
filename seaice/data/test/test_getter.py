from datetime import date
from unittest.mock import patch
import copy
import datetime as dt
import os
import unittest

from nose.tools import assert_equals, assert_true, raises
import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt

from seaice.data.errors import DateOutOfRangeError
from seaice.data.errors import YearMonthOutOfRangeError
import seaice.data.getter as getter
import seaice.data.gridset_filters as gridset_filters
import seaice.data.locator as locator
from .util import mock_today
import seaice.nasateam as nt

TEST_DATA = os.path.join(os.path.dirname(__file__),
                         os.path.pardir, os.path.pardir, os.path.pardir,
                         'test_data', 'seaice.data')
SOUTH_DAILY_FILE = os.path.join(TEST_DATA, 'nt_19871118_f08_v01_s.bin')
NORTH_DAILY_FILE = os.path.join(TEST_DATA, 'nt_20010107_f13_v01_n.bin')
OCEAN = 0
ICE = 1
COAST = 253
LAND = 254
MISSING = 255
GRIDSET_STUB = {'data': np.array([]), 'metadata': {'period': None,
                                                   'temporality': 'D',
                                                   'period_index': pd.PeriodIndex([], freq='D'),
                                                   'valid_data_range': (0, 100),
                                                   'flags': {},
                                                   'missing_value': None,
                                                   'hemi': 'N',
                                                   'files': []}}


class Test_concentration_daily(unittest.TestCase):

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.getter.empty_gridset')
    @patch('os.walk')
    def test_daily_no_file_gets_empty_grid(self, mock_walk, mock_empty_gridset,
                                           mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []

        # no files found
        mock_walk.return_value = [('/anyroot', [], [])]

        date_ = date(2015, 9, 1)
        hemisphere = nt.NORTH
        search_paths = ['/anyroot']

        mock_empty_gridset.return_value = {
            'data': np.full((448, 304), 255, dtype=np.int),
            'metadata': {}
        }

        # act
        getter.concentration_daily(hemisphere, date_, search_paths)

        # assert
        getter.empty_gridset.assert_called_with((448, 304), 'D')

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.gridset_filters._interpolate_missing')
    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    def test_daily_single_file_not_interpolated(self, mock_daily_file_path,
                                                _mockgridset_by_filelist,
                                                mock__interpolate_missing,
                                                mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []

        files = ['files.1_s.bin']
        gridset = {'data': [], 'metadata': {'files': []}}

        mock_daily_file_path.return_value = files
        _mockgridset_by_filelist.return_value = gridset
        mock__interpolate_missing.return_value = []

        date_ = date(2015, 9, 1)
        hemisphere = nt.NORTH
        search_paths = ['/anyroot']

        # act
        getter.concentration_daily(hemisphere, date_, search_paths, 1)

        # assert
        getter._concentration_gridset_by_filelist.assert_called_with(files)
        gridset_filters._interpolate_missing.assert_not_called()

    @mock_today(1995, 11, 24)
    @raises(DateOutOfRangeError)
    def test_daily_throws_error_for_dates_today_or_later(self, ):
        getter.concentration_daily(nt.NORTH, date(1995, 11, 24), ['/who/cares'])

    @mock_today(1990, 11, 24)
    @raises(DateOutOfRangeError)
    def test_daily_throws_error_for_future_date(self, ):
        getter.concentration_daily(nt.NORTH, date(1992, 1, 10), ['/who/cares'])

    @raises(DateOutOfRangeError)
    def test_daily_throws_error_before_october_26_1978(self, ):
        getter.concentration_daily(nt.NORTH, date(1978, 10, 25), ['/who/cares'])

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @mock_today(2014, 11, 24)
    def test_daily_works_with_yesterday(self, mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []
        actual = getter.concentration_daily(nt.NORTH, date(2014, 11, 23), ['/who/cares'])
        assert_equals(actual['data'].shape, (448, 304))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_daily_works_with_october_26_1978(self, mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []
        actual = getter.concentration_daily(nt.NORTH, date(1978, 10, 26), ['/who/cares'])
        assert_equals(actual['data'].shape, (448, 304))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.gridset_filters._interpolate_missing')
    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    def test_interpolation_with_skipped_day_in_SMMR_period(self,
                                                           mock_daily_file_path,
                                                           mock__gridset_by_filelist,
                                                           mock__interpolate_missing,
                                                           mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []

        files = ['nt_19810529_n07_v1.1_s.bin',
                 'nt_19810531_n07_v1.1_s.bin']
        gridset = {'data': np.full((2, 2, 2), 4, dtype=np.int),
                   'metadata': {'files': files}}

        mock_daily_file_path.return_value = files
        mock__gridset_by_filelist.return_value = gridset

        mock__interpolate_missing.return_value = np.full((2, 2), 4, dtype=np.int)

        interpolation_radius = 1

        nt_hemi = {'short_name': 'N'}
        anydate = dt.date(1981, 5, 30)
        actual_gridset = getter.concentration_daily(nt_hemi,
                                                    anydate,
                                                    ['/anypaths'],
                                                    interpolation_radius=interpolation_radius)
        actual = actual_gridset['metadata']['files']

        expected = ['nt_19810529_n07_v1.1_s.bin', 'nt_19810531_n07_v1.1_s.bin']

        self.assertEqual(actual, expected)


class Test_concentration_daily___failed_qa_logic(unittest.TestCase):

    def setUp(self):
        self.day_before_grid = np.full(nt.NORTH['shape'], 1, dtype=np.int)

        target_grid = np.full(nt.NORTH['shape'], 2, dtype=np.int)
        target_grid[0:3, 0:3] = nt.FLAGS['missing']
        self.target_grid = target_grid.copy()

        self.day_after_grid = np.full(nt.NORTH['shape'], 11, dtype=np.int)

        self.cube = np.dstack([self.day_before_grid, target_grid, self.day_after_grid])

        target_grid[0:3, 0:3] = (1 + 11) / 2
        self.interpolated_grid = target_grid.copy()

        self.empty_grid = np.full(nt.NORTH['shape'], nt.FLAGS['missing'], dtype=np.int)

        self.target_date = dt.date(1980, 10, 25)

        self.file_list = ['nt_19801024_n07_v1.1_n.bin',
                          'nt_19801025_n07_v1.1_n.bin',
                          'nt_19801026_n07_v1.1_n.bin']

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_returns_bad_data_gridset(self,
                                      mock_get_bad_days_for_hemisphere,
                                      mock_daily_file_path,
                                      mock__concentration_gridset_by_filelist):
        interpolation_radius = 0
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = self.file_list[1:2]
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.target_grid,
                   'metadata': {'files': file_list}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = getter.concentration_daily(nt.NORTH,
                                            self.target_date,
                                            ['/who/cares'],
                                            interpolation_radius=interpolation_radius)
        expected_grid = self.target_grid
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = self.file_list[1:2]
        self.assertEqual(actual['metadata']['files'], expected_files)


class Test_concentration_monthly(unittest.TestCase):

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.getter.empty_gridset')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_gets_data_when_at_least_twenty_days_present(
            self,
            mock_monthly_file_path,
            mock_all_daily_file_paths_for_month,
            mock_empty_gridset,
            _mockgridset_by_filelist
    ):
        locator.all_daily_file_paths_for_month.return_value = ['nt_20120901_f08_v01_n.bin'] * 20
        locator.monthly_file_path.return_value = 'nt_201209_f08_v01_n.bin'
        getter.empty_gridset.return_value = None
        getter._concentration_gridset_by_filelist.return_value = {
            'data': np.ma.array([1, 2]),
            'metadata': {}
        }

        year = 2012
        month = 9
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        getter.concentration_monthly(hemisphere, year, month, search_paths)

        getter._concentration_gridset_by_filelist.assert_called_with(['nt_201209_f08_v01_n.bin'])

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.getter.empty_gridset')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_gets_data_when_more_than_twenty_files_present_simmr(
            self,
            mock_monthly_file_path,
            mock_all_daily_file_paths_for_month,
            mock_empty_gridset,
            _mockgridset_by_filelist
    ):
        locator.all_daily_file_paths_for_month.return_value = ['nt_19781101_n07_v01_n.bin'] * 20
        locator.monthly_file_path.return_value = 'nt_197811_n07_v01_n.bin'
        getter.empty_gridset.return_value = None
        getter._concentration_gridset_by_filelist.return_value = {
            'data': np.ma.array([1, 2]),
            'metadata': {}
        }

        year = 1978
        month = 11
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        actual = getter.concentration_monthly(hemisphere, year, month, search_paths)

        getter._concentration_gridset_by_filelist.assert_called_with(['nt_197811_n07_v01_n.bin'])
        npt.assert_array_equal(actual['data'], np.ma.array([1, 2]))

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.getter.empty_gridset')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_uses_daily_for_nrt(
            self,
            mock_monthly_file_path,
            mock_all_daily_file_paths_for_month,
            mock_empty_gridset,
            _mockgridset_by_filelist
    ):
        daily_files = ['nt_20120915_f08_v01_n.bin'] * 20

        locator.all_daily_file_paths_for_month.return_value = daily_files
        locator.monthly_file_path.return_value = None
        getter.empty_gridset.return_value = None

        day1_grid = np.ma.array([[10., 30.], [50., 60.]])
        day2_grid = np.ma.array([[20., 50.], [80., 100.]])
        getter._concentration_gridset_by_filelist.return_value = {
            'data': np.ma.dstack([day1_grid, day2_grid]),
            'metadata': {'missing_value': 255., 'valid_data_range': (0., 100.)}
        }

        year = 1979
        month = 3
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        actual = getter.concentration_monthly(hemisphere, year, month, search_paths)
        expected = np.ma.array([[15., 40.], [65., 80.]])

        getter._concentration_gridset_by_filelist.assert_called_with(daily_files)
        npt.assert_array_equal(expected, actual['data'])

    @patch('seaice.data.getter.empty_gridset')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_under_threshold_empty_grid(self, mock_monthly_file_path,
                                                mock_all_daily_file_paths_for_month,
                                                mock_empty_gridset):
        locator.all_daily_file_paths_for_month.return_value = []
        locator.monthly_file_path.return_value = 'nt_201209_f08_v01_n.bin'
        getter.empty_gridset.return_value = None

        year = 2012
        month = 9
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        getter.concentration_monthly(hemisphere, year, month, search_paths)

        getter.empty_gridset.assert_called_with((448, 304), 'M')

    @patch('seaice.data.getter.empty_gridset')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_missing_empty_grid(self, mock_monthly_file_path,
                                        mock_all_daily_file_paths_for_month,
                                        mock_empty_gridset):
        locator.all_daily_file_paths_for_month.return_value = []
        locator.monthly_file_path.return_value = None
        getter.empty_gridset.return_value = None

        year = 2012
        month = 9
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        getter.concentration_monthly(hemisphere, year, month, search_paths)

        getter.empty_gridset.assert_called_with((448, 304), 'M')

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', date(2005, 4, 30))
    @patch('seaice.data.getter._concentration_average_gridset_from_daily_filelist')
    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.getter.double_weight_smmr_files')
    @patch('seaice.data.locator.all_daily_file_paths_for_month')
    @patch('seaice.data.locator.monthly_file_path')
    def test_monthly_uses_daily_when_final_month_is_outside_of_valid_final_data(
            self,
            mock_monthly_file_path,
            mock_all_daily_file_paths_for_month,
            mock_double_weight_smmr_files,
            mock__concentration_gridset_by_filelist,
            mock__concentration_average_gridset_from_daily_filelist
    ):
        daily_files = ['some', 'daily', 'files']

        mock_monthly_file_path.return_value = ['final_monthly_file']
        mock_all_daily_file_paths_for_month.return_value = daily_files
        mock_double_weight_smmr_files.return_value = daily_files
        mock__concentration_gridset_by_filelist.return_value = {'data': np.array([]),
                                                                'metadata': {}}

        hemisphere = nt.NORTH
        year = 2005
        month = 5
        search_paths = ['wherever']

        getter.concentration_monthly(hemisphere, year, month, search_paths, 3)

        # technically _concentration_gridset_by_filelist is called by
        # _concentration_average_gridset_from_daily_filelist, but here they are
        # both mocked, so they return right away and we can only worry about
        # which of these two functions concentration_monthly() calls directly
        getter._concentration_gridset_by_filelist.assert_not_called()
        getter._concentration_average_gridset_from_daily_filelist.assert_called_with(daily_files)

    @mock_today(1995, 11, 24)
    @raises(YearMonthOutOfRangeError)
    def test_monthly_throws_error_for_current_month(self):
        getter.concentration_monthly(nt.NORTH, 1995, 11, ['/who/cares'])

    @mock_today(2014, 11, 24)
    @raises(YearMonthOutOfRangeError)
    def test_monthly_throws_error_for_future_month(self):
        getter.concentration_monthly(nt.NORTH, 2014, 12, ['/who/cares'])

    @mock_today(2014, 11, 24)
    def test_monthly_works_with_last_month(self):
        actual = getter.concentration_monthly(nt.NORTH, 2014, 10, ['/who/cares'])
        assert_equals(actual['data'].shape, (448, 304))

    def test_monthly_works_with_october_1978(self):
        actual = getter.concentration_monthly(nt.NORTH, 1978, 10, ['/who/cares'])
        assert_equals(actual['data'].shape, (448, 304))

    @raises(YearMonthOutOfRangeError)
    def test_monthly_throws_error_before_october_1978(self):
        getter.concentration_monthly(nt.NORTH, 1978, 9, ['/who/cares'])


class Test_concentration_seasonal(unittest.TestCase):
    @patch('seaice.data.getter.concentration_monthly')
    def test_metadata(self, _mock_concentration_monthly):
        getter.concentration_monthly.side_effect = [
            {
                'data': np.ma.array([]),
                'metadata': {'files': ['nt_201209_f08_v01_n.bin']}
            },
            {
                'data': np.ma.array([]),
                'metadata': {'files': ['nt_201210_f08_v01_n.bin']}
            },
            {
                'data': np.ma.array([]),
                'metadata': {'files': ['nt_201211_f08_v01_n.bin']}
            }
        ]

        year = 2012
        months = (9, 10, 11)
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        actual = getter.concentration_seasonal(hemisphere, year, months, search_paths)

        expected_metadata = {
            'files': [['nt_201209_f08_v01_n.bin'],
                      ['nt_201210_f08_v01_n.bin'],
                      ['nt_201211_f08_v01_n.bin']],
            'temporality': 'seasonal',
            'hemi': 'N',
            'season': (2012, (9, 10, 11)),
            'search_paths': ['wherever'],
            'valid_data_range': (0.0, 100.0),
            'missing_value': 255,
            'flags': {
                'pole': 251,
                'unused': 252,
                'coast': 253,
                'land': 254
            }
        }

        for key, expected_value in expected_metadata.items():
            self.assertEqual(actual['metadata'][key], expected_value)

    @patch('seaice.data.getter.concentration_monthly')
    def test_averages_monthly_data(self, _mock_concentration_monthly):
        getter.concentration_monthly.side_effect = [
            {
                'data': np.ma.array([[5, 7],
                                     [5, 7]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[9, 3.5],
                                     [9, 3.5]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[10, 6],
                                     [10, 6]]),
                'metadata': {'files': []}
            }
        ]

        expected_data = np.array([[8, 5.5],
                                  [8, 5.5]])

        year = 2012
        months = (9, 10, 11)
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        actual = getter.concentration_seasonal(hemisphere, year, months, search_paths)

        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 2012, 9, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 2012, 10, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 2012, 11, ['wherever'], 20
        )

        npt.assert_array_equal(actual['data'], expected_data)

    @patch('seaice.data.getter.concentration_monthly')
    def test_uses_december_from_previous_year(self, _mock_concentration_monthly):
        getter.concentration_monthly.return_value = {
            'data': np.ma.array([[]]),
            'metadata': {'files': []}
        }

        year = 2012
        months = (12, 1, 2)
        hemisphere = nt.SOUTH
        search_paths = ['wherever']
        min_days_for_valid_month = 20

        getter.concentration_seasonal(hemisphere,
                                      year,
                                      months,
                                      search_paths,
                                      min_days_for_valid_month)

        getter.concentration_monthly.assert_any_call(
            nt.SOUTH, 2011, 12, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.SOUTH, 2012, 1, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.SOUTH, 2012, 2, ['wherever'], 20
        )

    @patch('seaice.data.getter.concentration_monthly')
    def test_does_not_average_missing_but_fills_with_flags(self, _mock_concentration_monthly):
        getter.concentration_monthly.side_effect = [
            {
                'data': np.ma.array([[255, 255, 255]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[9, 5, 251]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[10, 6, 251]]),
                'metadata': {'files': []}
            }
        ]

        year = 2012
        months = (9, 10, 11)
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        expected_data = np.array([[9.5, 5.5, 251]])

        actual = getter.concentration_seasonal(hemisphere, year, months, search_paths)

        npt.assert_array_equal(actual['data'], expected_data)

    @patch('seaice.data.getter.concentration_monthly')
    def test_takes_values_from_one_month_if_others_are_missing(
            self,
            _mock_concentration_monthly
    ):
        getter.concentration_monthly.side_effect = [
            {
                'data': np.ma.array([[255, 255, 255]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[255, 255, 255]]),
                'metadata': {'files': []}
            },
            {
                'data': np.ma.array([[10, 6, 7]]),
                'metadata': {'files': []}
            }
        ]

        year = 1988
        months = (12, 1, 2)
        hemisphere = nt.NORTH
        search_paths = ['wherever']

        expected_data = np.array([[10, 6, 7]])

        actual = getter.concentration_seasonal(hemisphere, year, months, search_paths)

        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 1987, 12, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 1988, 1, ['wherever'], 20
        )
        getter.concentration_monthly.assert_any_call(
            nt.NORTH, 1988, 2, ['wherever'], 20
        )
        npt.assert_array_equal(actual['data'], expected_data)


class Test_concentration_seasonal_over_years(unittest.TestCase):
    @patch('seaice.data.getter.concentration_seasonal')
    def test_calls_concentration_seasonal_for_every_year_inclusive(
            self,
            _mock_concentration_seasonal
    ):
        months = (12, 1, 2)
        hemisphere = nt.NORTH
        search_paths = ['wherever']
        min_valid_days = 20

        years = [1980, 1981, 1982, 1983, 1984,
                 1985, 1986, 1987, 1988, 1989,
                 1990, 1991, 1992, 1993, 1994,
                 1995, 1996, 1997, 1998, 1999,
                 2000]

        start_year = years[0]
        end_year = years[-1]

        getter.concentration_seasonal_over_years(
            hemisphere, start_year, end_year, months, search_paths, min_valid_days
        )

        for year in years:
            getter.concentration_seasonal.assert_any_call(
                hemisphere,
                year,
                months,
                search_paths,
                min_valid_days
            )

    @patch('seaice.data.getter.concentration_seasonal')
    def test_data_from_each_season_is_stacked(self, _mock_concentration_seasonal):
        grid0 = np.array([[1, 1],
                          [2, 2]])
        grid1 = np.array([[2, 9],
                          [3, 7]])
        grid2 = np.array([[4, 9],
                          [3, 5]])

        getter.concentration_seasonal.side_effect = [
            {
                'data': grid0,
                'metadata': {'files': [],
                             'valid_data_range': (),
                             'flags': {},
                             'missing_value': None}
            },
            {
                'data': grid1,
                'metadata': {'files': [],
                             'valid_data_range': (),
                             'flags': {},
                             'missing_value': None}
            },
            {
                'data': grid2,
                'metadata': {'files': [],
                             'valid_data_range': (),
                             'flags': {},
                             'missing_value': None}
            }
        ]
        months = (3, 4, 5)
        hemisphere = nt.NORTH
        search_paths = ['wherever']
        min_valid_days = 20

        start_year = 1980
        end_year = 1982

        actual = getter.concentration_seasonal_over_years(
            hemisphere, start_year, end_year, months, search_paths, min_valid_days
        )

        expected_data = np.dstack([grid0, grid1, grid2])

        npt.assert_array_equal(actual['data'], expected_data)

    @patch('seaice.data.getter.concentration_seasonal')
    def test_metadata(self, _mock_concentration_seasonal):
        the_grid = np.array([[0, 0],
                             [0, 0]])

        getter.concentration_seasonal.side_effect = [
            {
                'data': the_grid,
                'metadata': {
                    'files': ['file0'],
                    'temporality': 'seasonal',
                    'hemi': 'N',
                    'season': (2012, (9, 10, 11)),
                    'search_paths': ['wherever'],
                    'valid_data_range': (0.0, 100.0),
                    'missing_value': 255,
                    'flags': {
                        'pole': 251,
                        'unused': 252,
                        'coast': 253,
                        'land': 254
                    }
                }
            },
            {
                'data': the_grid,
                'metadata': {
                    'files': ['file1'],
                    'temporality': 'seasonal',
                    'hemi': 'N',
                    'season': (2012, (9, 10, 11)),
                    'search_paths': ['wherever'],
                    'valid_data_range': (0.0, 100.0),
                    'missing_value': 255,
                    'flags': {
                        'pole': 251,
                        'unused': 252,
                        'coast': 253,
                        'land': 254
                    }
                }
            },
            {
                'data': the_grid,
                'metadata': {
                    'files': ['file2'],
                    'temporality': 'seasonal',
                    'hemi': 'N',
                    'season': (2012, (9, 10, 11)),
                    'search_paths': ['wherever'],
                    'valid_data_range': (0.0, 100.0),
                    'missing_value': 255,
                    'flags': {
                        'pole': 251,
                        'unused': 252,
                        'coast': 253,
                        'land': 254
                    }
                }
            }
        ]

        months = (3, 4, 5)
        hemisphere = nt.NORTH
        search_paths = ['wherever']
        min_valid_days = 20
        start_year = 1980
        end_year = 1982

        actual = getter.concentration_seasonal_over_years(
            hemisphere, start_year, end_year, months, search_paths, min_valid_days
        )

        expected_metadata = {
            'files': [['file0'], ['file1'], ['file2']],
            'flags': {
                'pole': 251,
                'unused': 252,
                'coast': 253,
                'land': 254
            },
            'valid_data_range': (0.0, 100.0),
            'missing_value': 255,
        }

        self.assertEqual(actual['metadata'], expected_metadata)


class Test_extent_daily_median(unittest.TestCase):
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.getter.concentration_daily')
    def test_extent_daily_median_calls_daily_once_per_year(self, mock_concentration_daily,
                                                           mock_get_bad_days):
        mock_get_bad_days.return_value = []

        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        dayofyear = 7
        mock_concentration_daily.return_value = GRIDSET_STUB

        getter.extent_daily_median(hemi, start_year, end_year, dayofyear,
                                   search_paths=TEST_DATA, interpolation_radius=0)

        for year in [1981, 1982, 1983]:
            getter.concentration_daily.assert_any_call(nt.NORTH, dt.date(year, 1, 7),
                                                       TEST_DATA, 0)

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.getter.concentration_daily')
    def test_extent_daily_median_passes_all_parameters(self, mock_concentration_daily,
                                                       mock_get_bad_days):
        mock_get_bad_days.return_value = []

        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        dayofyear = 7

        mock_concentration_daily.return_value = GRIDSET_STUB

        getter.extent_daily_median(hemi, start_year, end_year, dayofyear,
                                   search_paths=TEST_DATA, interpolation_radius=0)

        for year in [1981, 1982, 1983]:
            getter.concentration_daily.assert_any_call(nt.NORTH, dt.date(year, 1, 7), TEST_DATA, 0)

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.getter.concentration_daily')
    def test_extent_daily_median_handles_doy_366(self, mock_concentration_daily,
                                                 mock_get_bad_days):
        mock_get_bad_days.return_value = []

        hemi = nt.NORTH
        start_year = 2000
        end_year = 2001
        dayofyear = 366

        mock_concentration_daily.return_value = GRIDSET_STUB

        getter.extent_daily_median(hemi, start_year, end_year, dayofyear=dayofyear,
                                   search_paths=TEST_DATA, interpolation_radius=0)

        # day 366 of a leap year is Dec 31
        getter.concentration_daily.assert_any_call(nt.NORTH, dt.date(2000, 12, 31), TEST_DATA, 0)

        # "day 366" of a non-leap year is Jan 1 of the next year
        getter.concentration_daily.assert_any_call(nt.NORTH, dt.date(2002, 1, 1), TEST_DATA, 0)

    @patch('seaice.data.getter.concentration_daily')
    def test_extent_daily_median_returns_grid(self, mock_concentration_daily):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        dayofyear = 7

        day_grid = np.zeros(nt.NORTH['shape'])

        gridset = copy.deepcopy(GRIDSET_STUB)
        gridset['data'] = day_grid
        mock_concentration_daily.return_value = gridset

        actual = getter.extent_daily_median(hemi, start_year, end_year, dayofyear,
                                            search_paths=TEST_DATA, interpolation_radius=0,
                                            allow_bad_dates=True)

        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_equals(expected, actual['data'].shape)

    @patch('seaice.data.getter.concentration_daily')
    def test_extent_daily_median_metadata(self, mock_daily):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        dayofyear = 7

        file_1981 = ['anyroot/nt_19810107_f17_v1.1_n.bin']
        file_1982 = ['anyroot/nt_19820107_f17_v1.1_n.bin']
        file_1983 = ['anyroot/nt_19830107_f17_v1.1_n.bin']

        gridsets = []
        for filelist in [file_1981, file_1982, file_1983]:
            gridset = copy.deepcopy(GRIDSET_STUB)
            gridset['metadata']['files'] = filelist
            gridsets.append(gridset)

        getter.concentration_daily.side_effect = gridsets

        actual = getter.extent_daily_median(hemi, start_year, end_year, dayofyear,
                                            search_paths=TEST_DATA, interpolation_radius=0,
                                            allow_bad_dates=True)

        expected = {'years': [1981, 1982, 1983], 'dayofyear': 7,
                    'files': [file_1981, file_1982, file_1983],
                    'period_index': [pd.PeriodIndex([], freq='D')] * 3}

        for key in ['years', 'dayofyear', 'files']:
            self.assertEqual(expected[key], actual['metadata'][key])

        for index, expected in enumerate(expected['period_index']):
            pdt.assert_index_equal(expected, actual['metadata']['period_index'][index])


class Test_extent_monthly_median(unittest.TestCase):

    @patch('seaice.data.getter.concentration_monthly')
    def test_extent_monthly_median_calls_concentration_monthly_once_per_year(
            self, mock_concentration_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1
        extent_threshold = 50

        month_grid = np.zeros(nt.NORTH['shape'])
        gridset = GRIDSET_STUB
        gridset['data'] = month_grid
        mock_concentration_monthly.return_value = gridset

        getter.extent_monthly_median(hemi, start_year, end_year, month,
                                     search_paths=TEST_DATA,
                                     extent_threshold=extent_threshold)

        for year in [1981, 1982, 1983]:
            getter.concentration_monthly.assert_any_call(nt.NORTH, year, month, TEST_DATA,
                                                         nt.MINIMUM_DAYS_FOR_VALID_MONTH)

    @patch('seaice.data.getter.concentration_monthly')
    def test_extent_monthly_median_returns_grid(self, mock_concentration_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1
        extent_threshold = 51

        month_grid = np.zeros(nt.NORTH['shape'])
        gridset = GRIDSET_STUB
        gridset['data'] = month_grid
        mock_concentration_monthly.return_value = gridset

        actual = getter.extent_monthly_median(hemi, start_year, end_year, month,
                                              search_paths=TEST_DATA,
                                              extent_threshold=extent_threshold)

        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_equals(expected, actual['data'].shape)

    @patch('seaice.data.getter.concentration_monthly')
    def test_extent_monthly_median_metadata(self, mock_concentration_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1
        extent_threshold = 50

        file_1981 = ['anyroot/nt_198101_f17_v1.1_n.bin']
        file_1982 = ['anyroot/nt_198201_f17_v1.1_n.bin']
        file_1983 = ['anyroot/nt_198301_f17_v1.1_n.bin']

        gridsets = []
        for filelist in [file_1981, file_1982, file_1983]:
            gridset = copy.deepcopy(GRIDSET_STUB)
            gridset['metadata']['files'] = filelist
            gridsets.append(gridset)

        getter.concentration_monthly.side_effect = gridsets

        actual = getter.extent_monthly_median(hemi, start_year, end_year, month,
                                              search_paths=TEST_DATA,
                                              extent_threshold=extent_threshold)

        expected = {'month': 1,
                    'years': [1981, 1982, 1983],
                    'files': [file_1981, file_1982, file_1983],
                    'valid_data_range': (0, 1),
                    'flags': {'coast': 253, 'land': 254, 'unused': 252, 'coast': 253, 'pole': 251},
                    'missing_value': 255}
        assert_equals(expected, actual['metadata'])


class Test__period_index_from_file_list(unittest.TestCase):

    def test_daily_files(self):
        expected = pd.PeriodIndex(['2001-01-07', '1987-11-18'], freq='D')
        file_list = [NORTH_DAILY_FILE, SOUTH_DAILY_FILE]

        actual = getter._period_index_from_file_list(file_list)

        pdt.assert_index_equal(actual, expected)

    def test_monthly_files(self):
        expected = pd.PeriodIndex(['2001-01', '1987-11'], freq='M')
        file_list = ['nt_200101_f08_v01_s.bin', 'nt_198711_f08_v01_s.bin']

        actual = getter._period_index_from_file_list(file_list)

        pdt.assert_index_equal(actual, expected)


class Test__concentration_gridset_by_filelist(unittest.TestCase):

    def test_gridset_by_filelist_south_with_two_files(self):
        expected = (332, 316, 2)
        file_list = [SOUTH_DAILY_FILE, SOUTH_DAILY_FILE]
        expected_files = file_list
        actual = getter._concentration_gridset_by_filelist(file_list)

        assert_equals(actual['data'].shape, expected)
        assert_equals(actual['metadata']['files'], expected_files)
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['1987-11-18', '1987-11-18'], freq='D'))

    def test_gridset_by_filelist_north_with_one_file(self):
        expected_shape = (448, 304)

        actual = getter._concentration_gridset_by_filelist([NORTH_DAILY_FILE])
        actual_shape = actual['data'].shape

        assert_equals(actual_shape, expected_shape)
        pdt.assert_index_equal(actual['metadata']['period_index'],
                               pd.PeriodIndex(['2001-01-07'], freq='D'))


class Test__concentration_average_gridset_from_daily_filelist(unittest.TestCase):

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    def test_retains_flagged_values(self, mocked_concentration_gridset_by_filelist):

        grid = np.ma.array([[251, 20],
                            [30, 40]])

        cube = np.ma.dstack((grid, grid, grid))
        gridset = {'data': cube, 'metadata': {'missing_value': 255.,
                                              'valid_data_range': (0., 100.)}}
        mocked_concentration_gridset_by_filelist.return_value = gridset

        expected = copy.deepcopy(grid)

        actual = getter._concentration_average_gridset_from_daily_filelist(['file_list'])

        npt.assert_array_equal(expected, actual['data'])
        npt.assert_array_equal(expected.data, actual['data'].data)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    def test_retains_flagged_values_with_missing(self, mocked_concentration_gridset_by_filelist):

        grid = np.ma.array([[251, 20],
                            [30, 40]])

        grid2 = np.ma.array([[251, 255.],
                             [30, 40]])

        cube = np.ma.dstack((grid, grid2, grid))
        gridset = {'data': cube, 'metadata': {'missing_value': 255.,
                                              'valid_data_range': (0., 100.)}}
        mocked_concentration_gridset_by_filelist.return_value = gridset

        expected = copy.deepcopy(grid)

        actual = getter._concentration_average_gridset_from_daily_filelist(['file_list'])

        npt.assert_array_equal(expected, actual['data'])

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    def test_flagged_values_become_missing_with_missing_flag(
            self, mocked_concentration_gridset_by_filelist):

        grid = np.array([[251, 20],
                         [30, 40]])

        grid2 = np.array([[255., 20.],
                          [30, 40]])

        cube = np.ma.dstack((grid, grid2, grid))
        gridset = {'data': cube, 'metadata': {'missing_value': 255.,
                                              'valid_data_range': (0., 100.)}}
        mocked_concentration_gridset_by_filelist.return_value = gridset

        expected = np.array([[255, 20],
                             [30, 40]])

        actual = getter._concentration_average_gridset_from_daily_filelist(['file_list'])

        npt.assert_array_equal(expected, actual['data'])
        npt.assert_array_equal(expected.data, actual['data'].data)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    def test_retains_missing_values(self, mocked_concentration_gridset_by_filelist):

        grid = np.array([[255, 20],
                         [30, 40]])

        grid2 = np.array([[255., 20.],
                          [30, 40]])

        cube = np.ma.dstack((grid, grid2, grid))
        gridset = {'data': cube, 'metadata': {'missing_value': 255.,
                                              'valid_data_range': (0., 100.)}}
        mocked_concentration_gridset_by_filelist.return_value = gridset

        expected = np.array([[255, 20],
                             [30, 40]])

        actual = getter._concentration_average_gridset_from_daily_filelist(['file_list'])

        npt.assert_array_equal(expected, actual['data'])
        npt.assert_array_equal(expected.data, actual['data'].data)


class Test_double_weight_smmr_files(unittest.TestCase):
    def test_does_not_affect_non_n07(self):
        paths = ['anyroot/nt_198101_f17_v1.1_n.bin', 'anyroot/nt_198201_f17_v1.1_n.bin']
        actual = getter.double_weight_smmr_files(paths)

        expected = paths

        self.assertEqual(actual, expected)

    def test_adds_repeat_of_n07_files(self):
        paths = ['anyroot/nt_198101_n07_v1.1_n.bin', 'anyroot/nt_198201_f17_v1.1_n.bin']
        actual = getter.double_weight_smmr_files(paths)

        expected = ['anyroot/nt_198101_n07_v1.1_n.bin'] + paths

        self.assertEqual(actual, expected)


class Test_empty_gridset(unittest.TestCase):

    def test_empty_grid_daily(self):
        shape = (127, 523)

        actual_grid = getter.empty_gridset(shape, 'D')

        assert_equals(shape, actual_grid['data'].shape)
        assert_equals(actual_grid['metadata']['empty_gridset'], True)
        assert_true(np.all(actual_grid['data'] == 255.))
        self.assertEqual(actual_grid['metadata']['temporality'], 'D')

    def test_empty_grid_monthly(self):
        shape = (127, 523)

        actual_grid = getter.empty_gridset(shape, 'M')

        assert_equals(shape, actual_grid['data'].shape)
        assert_equals(actual_grid['metadata']['empty_gridset'], True)
        assert_true(np.all(actual_grid['data'] == 255.))
        self.assertEqual(actual_grid['metadata']['temporality'], 'M')


class Test__extent_median(unittest.TestCase):
    def test_counts_ice_when_ice_fifty_percent_of_time(self):
        grid1 = np.array([[OCEAN, OCEAN],
                          [OCEAN, ICE]])

        grid2 = np.array([[OCEAN, OCEAN],
                          [ICE,   ICE]])

        data = np.dstack([grid1, grid2])

        actual = getter._extent_median(data)

        expected = np.array([[OCEAN, OCEAN],
                             [ICE,   ICE]])

        npt.assert_array_equal(actual, expected)

    def test_always_land_or_missing_becomes_land(self):
        grid1 = np.array([[OCEAN, LAND],
                          [OCEAN, OCEAN]])

        grid2 = np.array([[OCEAN, MISSING],
                          [OCEAN, OCEAN]])

        data = np.dstack([grid1, grid2])

        actual = getter._extent_median(data)

        expected = np.array([[OCEAN, LAND],
                             [OCEAN, OCEAN]])

        npt.assert_array_equal(actual, expected)

    def test_always_missing_becomes_land(self):
        grid1 = np.array([[OCEAN, MISSING],
                          [OCEAN, OCEAN]])

        grid2 = np.array([[OCEAN, MISSING],
                          [OCEAN, OCEAN]])

        data = np.dstack([grid1, grid2])

        actual = getter._extent_median(data)

        expected = np.array([[OCEAN, LAND],
                             [OCEAN, OCEAN]])

        npt.assert_array_equal(actual, expected)


class Test__flag_layer_from_cube(unittest.TestCase):
    anything = 123.528
    ignored = 825.321

    def test_with_single_layer(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1])

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_with_single_layer_from_2d_gridset(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1])
        flag_cube = np.ma.squeeze(flag_cube)

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_with_multiple_layers_same_flags(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid2 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_multiple_layers_with_flag_and_missing(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid2 = np.ma.array([[255, self.anything],
                             [self.anything, self.anything]],
                            mask=[[True, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube)

        # When a value that was flagged, gets a missing value in a different
        # layer we know that we have a shrinking pole hole or some other
        # magic. The nsidc0081 processing applies a standard mask for pole and
        # for land/coast/ocean.  Therefore we don't need to worry about the case
        # where a pole value goes missing in one layer, but is pole in all
        # other layers.
        expected = np.ma.array([[self.ignored, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[True, True],
                                     [True, True]])

        npt.assert_array_equal(expected.mask, actual.mask)

    def test_shrinking_pole_hole(self):
        grid1 = np.ma.array([[251, 251],
                             [self.anything, self.anything]],
                            mask=[[False, False],
                                  [True, True]])

        grid2 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_shrinking_pole_hole_flagged_then_missing_then_data_returns_data(self):
        grid1 = np.ma.array([[251, 251],
                             [self.anything, self.anything]],
                            mask=[[False, False],
                                  [True, True]])

        grid2 = np.ma.array([[251, 255],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid3 = np.ma.array([[251, 87],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2, grid3])

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, 87 + self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_with_differing_flag_values(self):
        grid1 = np.ma.array([[251, 251],
                             [self.anything, self.anything]],
                            mask=[[False, False],
                                  [True, True]])

        grid2 = np.ma.array([[251, 252],
                             [self.anything, self.anything]],
                            mask=[[False, False],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)

    def test_ignores_layer_of_all_missing(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid2 = np.ma.array([[255, 255],
                             [255, 255]],
                            mask=[[False, False],
                                  [False, False]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube, missing_value=255)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected.mask, actual.mask)

    def test_ignores_layer_of_all_missing_when_first(self):
        grid1 = np.ma.array([[255, 255],
                             [255, 255]],
                            mask=[[False, False],
                                  [False, False]])

        grid2 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        flag_cube = np.ma.dstack([grid1, grid2])

        actual = getter.flag_layer_from_cube(flag_cube, missing_value=255)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected.mask, actual.mask)

    def test_multiple_layers_with_flag_and_missing_and_one_missing_layer(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid2 = np.ma.array([[255, self.anything],
                             [self.anything, self.anything]],
                            mask=[[True, True],
                                  [True, True]])

        grid3 = np.ma.array([[255, 255],
                             [255, 255]],
                            mask=[[False, False],
                                  [False, False]])

        flag_cube = np.ma.dstack([grid1, grid2, grid3])

        actual = getter.flag_layer_from_cube(flag_cube, missing_value=255)

        # When a value that was flagged, gets a missing value in a different
        # layer we know that we have a shrinking pole hole or some other
        # magic. The nsidc0081 processing applies a standard mask for pole and
        # for land/coast/ocean.  Therefore we don't need to worry about the case
        # where a pole value goes missing in one layer, but is pole in all
        # other layers.
        expected = np.ma.array([[self.ignored, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[True, True],
                                     [True, True]])

        npt.assert_array_equal(expected.mask, actual.mask)

    def test_with_multiple_layers_same_flags_and_one_missing_layer(self):
        grid1 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid2 = np.ma.array([[251, self.anything],
                             [self.anything, self.anything]],
                            mask=[[False, True],
                                  [True, True]])

        grid3 = np.ma.array([[255, 255],
                             [255, 255]],
                            mask=[[False, False],
                                  [False, False]])

        flag_cube = np.ma.dstack([grid1, grid2, grid3])

        actual = getter.flag_layer_from_cube(flag_cube, missing_value=255)

        expected = np.ma.array([[251, self.ignored],
                                [self.ignored, self.ignored]],
                               mask=[[False, True],
                                     [True, True]])

        npt.assert_array_equal(expected, actual)
        npt.assert_array_equal(expected.mask, actual.mask)


class Test__rows_columns_from_goddard_nasateam_header(unittest.TestCase):

    def test_rows_columns_from_file(self):
        expected = (448, 304)
        with open(NORTH_DAILY_FILE, 'rb') as fp:
            header = fp.read(nt.NASATEAM_HEADER_LENGTH)
        actual = getter._rows_columns_from_goddard_nasateam_header(header)
        assert_equals(expected, actual)


class Test__scale_valid_data(unittest.TestCase):

    def test_scales_data(self):
        z = np.array([1., 2., 3., 4.])
        expected = np.array([1., .2, .3, 4.])
        actual = getter._scale_valid_data(z, (2, 3), 10)
        npt.assert_array_equal(expected, actual)


class Test_concentration_monthly_over_years(unittest.TestCase):
    monthly_stub = {'data': np.zeros(nt.NORTH['shape']),
                    'metadata': {'files': [],
                                 'valid_data_range': (0, 100),
                                 'flags': {},
                                 'missing_value': None,
                                 'period_index': pd.PeriodIndex([], freq='M')}}

    @patch('seaice.data.getter.concentration_monthly')
    def test_monthly_over_years_calls_monthly_once_per_year(self, mock_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1

        mock_monthly.return_value = self.monthly_stub

        getter.concentration_monthly_over_years(hemi, start_year, end_year, month,
                                                search_paths=TEST_DATA)

        for year in [1981, 1982, 1983]:
            getter.concentration_monthly.assert_any_call(nt.NORTH, year, 1, TEST_DATA,
                                                         nt.MINIMUM_DAYS_FOR_VALID_MONTH)

    @patch('seaice.data.getter.concentration_monthly')
    def test_monthly_over_years_data(self, mock_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1

        mock_monthly.return_value = self.monthly_stub

        actual = getter.concentration_monthly_over_years(hemi, start_year, end_year, month,
                                                         search_paths=TEST_DATA)

        rows, cols = nt.NORTH['shape']
        expected = (rows, cols, 3)
        assert_equals(expected, actual['data'].shape)

    @patch('seaice.data.getter.concentration_monthly')
    def test_monthly_over_years_metadata(self, mock_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1

        file_1981 = ['anyroot/nt_198101_f17_v1.1_n.bin']
        file_1982 = ['anyroot/nt_198201_f17_v1.1_n.bin']
        file_1983 = ['anyroot/nt_198301_f17_v1.1_n.bin']

        monthly_1981 = copy.deepcopy(self.monthly_stub)
        monthly_1981['metadata']['files'] = file_1981

        monthly_1982 = copy.deepcopy(self.monthly_stub)
        monthly_1982['metadata']['files'] = file_1982

        monthly_1983 = copy.deepcopy(self.monthly_stub)
        monthly_1983['metadata']['files'] = file_1983

        getter.concentration_monthly.side_effect = [monthly_1981, monthly_1982, monthly_1983]

        actual = getter.concentration_monthly_over_years(hemi, start_year, end_year, month,
                                                         search_paths=TEST_DATA)

        expected = {'flags': {},
                    'missing_value': None,
                    'valid_data_range': (0, 100),
                    'period_index': pd.PeriodIndex([], freq='M'),
                    'files': [file_1981, file_1982, file_1983]}

        pdt.assert_index_equal(expected.pop('period_index'),
                               actual['metadata'].pop('period_index'))

        assert_equals(expected, actual['metadata'])

    @patch('seaice.data.getter.concentration_monthly')
    def test_monthly_over_years_metadata_with_one_month_using_average(self, mock_monthly):
        hemi = nt.NORTH
        start_year = 1981
        end_year = 1983
        month = 1

        file_1981 = ['anyroot/nt_198101_f17_v1.1_n.bin']
        file_1982 = ['anyroot/nt_198201_f17_v1.1_n.bin']
        file_1983 = ['anyroot/nt_198301{d:02}_f17_v1.1_n.bin'.format(d=d) for d in range(1, 32)]

        monthly_1981 = copy.deepcopy(self.monthly_stub)
        monthly_1981['metadata']['files'] = file_1981

        monthly_1982 = copy.deepcopy(self.monthly_stub)
        monthly_1982['metadata']['files'] = file_1982

        monthly_1983 = copy.deepcopy(self.monthly_stub)
        monthly_1983['metadata']['files'] = file_1983

        getter.concentration_monthly.side_effect = [monthly_1981, monthly_1982, monthly_1983]

        actual = getter.concentration_monthly_over_years(hemi, start_year, end_year, month,
                                                         search_paths=TEST_DATA)

        expected = {
            'flags': {},
            'missing_value': None,
            'valid_data_range': (0, 100),
            'files': [file_1981, file_1982, file_1983],
            'period_index': pd.PeriodIndex([], freq='M')}

        pdt.assert_index_equal(expected.pop('period_index'),
                               actual['metadata'].pop('period_index'))
        assert_equals(expected, actual['metadata'])
