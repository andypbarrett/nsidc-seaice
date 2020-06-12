from unittest.mock import patch
import datetime as dt
import os
import unittest

from nose.tools import assert_equals, assert_true, assert_false, assert_raises
import numpy as np
import numpy.testing as npt
import pandas as pd

import seaice.data as sid
import seaice.data.api as api
import seaice.data.errors as e
import seaice.data.getter as getter
import seaice.data.gridset_filters as gf
import seaice.nasateam as nt


TEST_ROOT = [os.path.join(
    os.path.dirname(__file__),
    os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir,
    'test_data',
    'seaice.data'
)]


class Test_concentration_daily(unittest.TestCase):

    def test_concentration_daily(self):
        result = sid.concentration_daily(hemisphere=nt.NORTH, year=2001,
                                         month=1, day=7, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_false(np.all(result['data'] == 255.))
        assert_equals(expected, actual)

    def test_missing_day_returns_empty_grid(self):
        result = sid.concentration_daily(hemisphere=nt.NORTH, year=2002,
                                         month=1, day=1, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_true(np.all(result['data'] == 255.))
        assert_equals(expected, actual)

    def test_missing_day_raises_when_asked_to(self):
        assert_raises(e.SeaIceDataNoData, sid.concentration_daily,
                      hemisphere=nt.NORTH, year=2002,
                      month=1, day=1, search_paths=TEST_ROOT,
                      allow_empty_gridset=False)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.locator.daily_file_path')
    def test_with_bad_date_and_empty_gridset_not_allowed(self,
                                                         mock_daily_file_path,
                                                         mock_get_bad_days_for_hemisphere,
                                                         mock__concentration_gridset_by_filelist):
        files = ['doesnt_matter1.bin',
                 'doesnt_matter2.bin'
                 'doesnt_matter3.bin']
        mock_daily_file_path.return_value = files
        shape = (5, 5, 2)
        missing = 255
        mock__concentration_gridset_by_filelist.return_value = {
            'data': np.full(shape, missing, dtype=np.int),
            'metadata': {
                'period_index': pd.period_range('1980-10-21', '1980-10-23', freq='D'),
                'missing_value': 255,
                'files': files
            }
        }

        bad_dates = pd.period_range('1980-10-20', '1980-10-27', freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates

        with self.assertRaises(e.SeaIceDataNoData):
            sid.concentration_daily(nt.NORTH,
                                    1980, 10, 25,
                                    ['/who/cares'],
                                    interpolation_radius=0,
                                    allow_empty_gridset=False,
                                    allow_bad_dates=False)

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.gridset_filters._interpolate_missing')
    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    def test_daily_multiple_files_interpolated(self, mock_daily_file_path,
                                               _mockgridset_by_filelist, mock__interpolate_missing,
                                               mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []

        files = ['nt_20150831_n07_v1.1_s.bin',
                 'nt_20150901_n07_v1.1_s.bin',
                 'nt_20150902_n07_v1.1_s.bin']
        gridset = {'data': np.full((2, 2, 3), 2, dtype=np.int),
                   'metadata': {'files': files,
                                'period_index': pd.period_range(start='2015-08-31',
                                                                end='2015-09-02',
                                                                freq='D')}}

        mock_daily_file_path.return_value = files
        _mockgridset_by_filelist.return_value = gridset

        interpolated = np.full((2, 2), 2, dtype=np.int)
        mock__interpolate_missing.return_value = interpolated

        hemisphere = nt.NORTH
        search_paths = ['/anyroot']
        # act
        sid.concentration_daily(hemisphere, 2015, 9, 1, search_paths, interpolation_radius=1)

        # assert
        getter._concentration_gridset_by_filelist.assert_called_with(files)

        npt.assert_array_equal(mock__interpolate_missing.call_args[0][0], interpolated)
        npt.assert_array_equal(mock__interpolate_missing.call_args[0][1],
                               np.full((2, 2, 2), 2, dtype=np.int))

    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.gridset_filters._interpolate_missing')
    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    def test_no_interpolation_needed_only_includes_file_for_date(self,
                                                                 mock_daily_file_path,
                                                                 mock__gridset_by_filelist,
                                                                 mock__interpolate_missing,
                                                                 mock_get_bad_days_for_hemisphere):
        mock_get_bad_days_for_hemisphere.return_value = []

        files = ['nt_20112131_n07_v1.1_s.bin',
                 'nt_20120101_n07_v1.1_s.bin',
                 'nt_20120102_n07_v1.1_s.bin']
        gridset = {'data': np.full((2, 2, 3), 4, dtype=np.int),
                   'metadata': {'files': files,
                                'period_index': pd.period_range(start='2011-12-31',
                                                                periods=3,
                                                                freq='D')}}

        mock_daily_file_path.return_value = files
        mock__gridset_by_filelist.return_value = gridset

        mock__interpolate_missing.return_value = np.full((2, 2), 4, dtype=np.int)

        interpolation_radius = 1

        nt_hemi = nt.NORTH
        actual_gridset = sid.concentration_daily(nt_hemi,
                                                 2012,
                                                 1,
                                                 1,
                                                 ['/anypaths'],
                                                 interpolation_radius=interpolation_radius)
        actual = actual_gridset['metadata']['files']

        expected = ['nt_20120101_n07_v1.1_s.bin']

        self.assertEqual(actual, expected)


class Test_concentration_daily_average_over_date_range(unittest.TestCase):
    def test_concentration_daily_average_over_date_range(self):
        date_range = pd.DatetimeIndex(['2001-01-06', '2001-01-07'])
        result = sid.concentration_daily_average_over_date_range('N',
                                                                 date_range,
                                                                 search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_false(np.all(result['data'] == 255.))
        assert_equals(expected, actual)

    def test_different_from_each_day(self):
        date_range = pd.DatetimeIndex(['2001-01-06', '2001-01-07'])
        first = sid.concentration_daily(hemisphere=nt.NORTH, year=2001,
                                        month=1, day=6, search_paths=TEST_ROOT)
        last = sid.concentration_daily(hemisphere=nt.NORTH, year=2001,
                                       month=1, day=7, search_paths=TEST_ROOT)
        average = sid.concentration_daily_average_over_date_range('N',
                                                                  date_range,
                                                                  search_paths=TEST_ROOT)

        self.assertFalse(np.all(average['data'] == first['data']))
        self.assertFalse(np.all(average['data'] == last['data']))


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

        self.period_index = pd.period_range(start='1980-10-24', end='1980-10-26', freq='D')

        self.file_list = ['nt_19801024_n07_v1.1_n.bin',
                          'nt_19801025_n07_v1.1_n.bin',
                          'nt_19801026_n07_v1.1_n.bin']

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_good_day_interpolates_with_good_days_with_allow_bad_dates_false_and_empty_false(
            self,
            mock_get_bad_days_for_hemisphere,
            mock_daily_file_path,
            mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = False
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = []

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         self.target_date.year,
                                         self.target_date.month,
                                         self.target_date.day,
                                         ['/who/cares'],
                                         interpolation_radius=interpolation_radius,
                                         allow_empty_gridset=allow_empty_gridset,
                                         allow_bad_dates=allow_bad_dates)
        expected_grid = self.interpolated_grid
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = self.file_list
        self.assertEqual(actual['metadata']['files'], expected_files)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_good_day_doesnt_interpolate_with_bad_days(
            self,
            mock_get_bad_days_for_hemisphere,
            mock_daily_file_path,
            mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = False
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [
            pd.Period(self.target_date - dt.timedelta(1), 'D'),
            pd.Period(self.target_date + dt.timedelta(1), 'D')
        ]

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         self.target_date.year,
                                         self.target_date.month,
                                         self.target_date.day,
                                         ['/who/cares'],
                                         interpolation_radius=interpolation_radius,
                                         allow_empty_gridset=allow_empty_gridset,
                                         allow_bad_dates=allow_bad_dates)
        expected_grid = self.target_grid
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = self.file_list[1:2]
        self.assertEqual(actual['metadata']['files'], expected_files)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_raises_when_interpolation_attempt_with_all_bad_days_and_disallowing_bad(
            self,
            mock_get_bad_days_for_hemisphere,
            mock_daily_file_path,
            mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = False
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [
            pd.Period(self.target_date - dt.timedelta(1), 'D'),
            pd.Period(self.target_date, 'D'),
            pd.Period(self.target_date + dt.timedelta(1), 'D')
        ]

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list
        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        with self.assertRaises(e.SeaIceDataNoData):
            sid.concentration_daily(nt.NORTH,
                                    self.target_date.year,
                                    self.target_date.month,
                                    self.target_date.day,
                                    ['/who/cares'],
                                    interpolation_radius=interpolation_radius,
                                    allow_empty_gridset=allow_empty_gridset,
                                    allow_bad_dates=allow_bad_dates)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_bad_day_interpolates_with_good_days_despite_disallowing_bad(
            self,
            mock_get_bad_days_for_hemisphere,
            mock_daily_file_path,
            mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = False
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         self.target_date.year,
                                         self.target_date.month,
                                         self.target_date.day,
                                         ['/who/cares'],
                                         interpolation_radius=interpolation_radius,
                                         allow_empty_gridset=allow_empty_gridset,
                                         allow_bad_dates=allow_bad_dates)
        expected_grid = np.full(nt.NORTH['shape'], 6, dtype=np.int)
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = [self.file_list[0], self.file_list[2]]
        self.assertEqual(actual['metadata']['files'], expected_files)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_raises_exception_with_no_data_to_interpolate(self,
                                                          mock_get_bad_days_for_hemisphere,
                                                          mock_daily_file_path,
                                                          mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = True
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = []
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.empty_grid,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        with self.assertRaises(e.SeaIceDataNoData):
            sid.concentration_daily(nt.NORTH,
                                    self.target_date.year,
                                    self.target_date.month,
                                    self.target_date.day,
                                    ['/who/cares'],
                                    interpolation_radius=interpolation_radius,
                                    allow_empty_gridset=allow_empty_gridset,
                                    allow_bad_dates=allow_bad_dates)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_raises_exception_with_bad_data(self,
                                            mock_get_bad_days_for_hemisphere,
                                            mock_daily_file_path,
                                            mock__concentration_gridset_by_filelist):
        allow_empty_gridset = False
        allow_bad_dates = False
        interpolation_radius = 0
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = self.file_list[1:2]
        period_index = self.period_index[1:2]
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.target_grid,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        with self.assertRaises(e.SeaIceDataNoData):
            sid.concentration_daily(nt.NORTH,
                                    self.target_date.year,
                                    self.target_date.month,
                                    self.target_date.day,
                                    ['/who/cares'],
                                    interpolation_radius=interpolation_radius,
                                    allow_empty_gridset=allow_empty_gridset,
                                    allow_bad_dates=allow_bad_dates)

    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_raises_exception_with_no_data(self,
                                           mock_get_bad_days_for_hemisphere,
                                           mock_daily_file_path):
        allow_empty_gridset = False
        allow_bad_dates = True
        interpolation_radius = 0
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = []
        mock_daily_file_path.return_value = file_list

        with self.assertRaises(e.SeaIceDataNoData):
            sid.concentration_daily(nt.NORTH,
                                    self.target_date.year,
                                    self.target_date.month,
                                    self.target_date.day,
                                    ['/who/cares'],
                                    interpolation_radius=interpolation_radius,
                                    allow_empty_gridset=allow_empty_gridset,
                                    allow_bad_dates=allow_bad_dates)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_returns_interpolated_bad_data_gridset(self,
                                                   mock_get_bad_days_for_hemisphere,
                                                   mock_daily_file_path,
                                                   mock__concentration_gridset_by_filelist):
        allow_bad_dates = True
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [pd.Period(self.target_date, 'D')]

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}
        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         self.target_date.year,
                                         self.target_date.month,
                                         self.target_date.day,
                                         ['/who/cares'],
                                         interpolation_radius=interpolation_radius,
                                         allow_bad_dates=allow_bad_dates)
        expected_grid = self.interpolated_grid
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = self.file_list
        self.assertEqual(actual['metadata']['files'], expected_files)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.data.locator.daily_file_path')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_returns_empty_grid_when_all_bad_and_disallowed_bad_but_empty_allowed(
            self,
            mock_get_bad_days_for_hemisphere,
            mock_daily_file_path,
            mock__concentration_gridset_by_filelist):
        allow_bad_dates = False
        interpolation_radius = 1
        mock_get_bad_days_for_hemisphere.return_value = [
            pd.Period(self.target_date - dt.timedelta(1), 'D'),
            pd.Period(self.target_date, 'D'),
            pd.Period(self.target_date + dt.timedelta(1), 'D')
        ]

        file_list = self.file_list
        mock_daily_file_path.return_value = file_list

        gridset = {'data': self.cube,
                   'metadata': {'files': file_list,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}

        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         self.target_date.year,
                                         self.target_date.month,
                                         self.target_date.day,
                                         ['/who/cares'],
                                         interpolation_radius=interpolation_radius,
                                         allow_bad_dates=allow_bad_dates)
        expected_grid = self.empty_grid
        npt.assert_array_equal(actual['data'], expected_grid)

        expected_files = []
        self.assertEqual(actual['metadata']['files'], expected_files)

    @patch('seaice.data.getter._concentration_gridset_by_filelist')
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    @patch('seaice.data.locator.daily_file_path')
    def test_with_bad_date_and_empty_gridset_allowed(self,
                                                     mock_daily_file_path,
                                                     mock_get_bad_days_for_hemisphere,
                                                     mock__concentration_gridset_by_filelist):
        allow_bad_dates = False
        files = ['files.1_s.bin']
        mock_daily_file_path.return_value = files

        bad_dates = pd.period_range('1980-10-20', '1980-10-27', freq='D')
        mock_get_bad_days_for_hemisphere.return_value = bad_dates

        gridset = {'data': self.target_grid,
                   'metadata': {'files': files,
                                'missing_value': nt.FLAGS['missing'],
                                'period_index': self.period_index,
                                'valid_data_range': (0, 100)}}

        mock__concentration_gridset_by_filelist.return_value = gridset

        actual = sid.concentration_daily(nt.NORTH,
                                         1980,
                                         10,
                                         25,
                                         ['/who/cares'],
                                         interpolation_radius=0,
                                         allow_bad_dates=allow_bad_dates)
        expected = np.full((448, 304), 255, dtype=np.int)

        npt.assert_array_equal(actual['data'], expected)


class Test_extent_daily(unittest.TestCase):

    def test_calls_ok(self):
        result = sid.extent_daily(hemisphere=nt.NORTH, year=2001,
                                  month=1, day=7, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_false(np.all(result['data'] == 255.))
        assert_equals(expected, actual)


class Test_extent_daily_median(unittest.TestCase):
    @patch('seaice.datastore.get_bad_days_for_hemisphere')
    def test_calls_ok(self, mock_get_bad_days):
        mock_get_bad_days.return_value = []
        result = sid.extent_daily_median(hemisphere=nt.NORTH, start_year=2001, end_year=2002,
                                         dayofyear=7, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_equals(expected, actual)


class Test_concentration_monthly(unittest.TestCase):

    def test_concentration_monthly_with_insufficent_daily_files(self):
        result = sid.concentration_monthly(hemisphere=nt.NORTH, year=2001,
                                           month=1, search_paths=TEST_ROOT,
                                           allow_empty_gridset=True)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_true(np.all(result['data'] == 255.))
        assert_equals(result['metadata']['empty_gridset'], True)
        assert_equals(expected, actual)

    def test_concentration_monthly_with_sufficient_daily_files(self):
        result = sid.concentration_monthly(hemisphere=nt.NORTH, year=2001,
                                           month=1, search_paths=TEST_ROOT,
                                           allow_empty_gridset=True,
                                           min_days_for_valid_month=2)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_false(np.all(result['data'] == 255.))
        assert_equals(expected, actual)
        assert_equals(result['metadata'].get('empty_gridset', False), False)

    def test_missing_month_returns_empty_grid(self):
        result = sid.concentration_monthly(hemisphere=nt.NORTH, year=2002,
                                           month=1, search_paths=TEST_ROOT,
                                           allow_empty_gridset=True)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_true(np.all(result['data'] == 255.))
        assert_equals(expected, actual)
        assert_equals(result['metadata']['empty_gridset'], True)

    def test_missing_month_raises_when_asked_to(self):
        assert_raises(e.SeaIceDataNoData, sid.concentration_monthly,
                      hemisphere=nt.NORTH, year=2002,
                      month=1, search_paths=TEST_ROOT,
                      allow_empty_gridset=False)


class Test_extent_monthly(unittest.TestCase):

    def test_calls_ok(self):
        result = sid.extent_monthly(hemisphere=nt.NORTH, year=2001, month=1, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_equals(expected, actual)


class Test_extent_monthly_median(unittest.TestCase):

    def test_calls_ok(self):
        result = sid.extent_monthly_median(hemisphere=nt.NORTH, start_year=2001, end_year=2002,
                                           month=1, search_paths=TEST_ROOT)
        actual = result['data'].shape
        rows, cols = nt.NORTH['shape']
        expected = (rows, cols)
        assert_equals(expected, actual)


class Test__filters(unittest.TestCase):
    def test_no_params(self):
        actual = api._filters()
        expected = []
        self.assertEqual(actual, expected)

    @patch('seaice.data.api.functools.partial')
    def test_drop_land(self, mock_partial):
        actual = api._filters(drop_land=True)
        expected = [mock_partial.return_value]

        mock_partial.assert_called_once_with(gf.drop_land, nt.FLAGS['land'], nt.FLAGS['coast'])
        self.assertEqual(actual, expected)

    def test_bad_dates(self):
        actual = api._filters(allow_bad_dates=False)
        expected = [gf.drop_bad_dates]
        self.assertEqual(actual, expected)

    def test_interpolate(self):
        actual = api._filters(interpolation_radius=1)
        expected = [gf.interpolate]
        self.assertEqual(actual, expected)

    def test_drop_invalid_ice_with_no_other_params(self):
        actual = api._filters(drop_invalid_ice=True)
        expected = []
        self.assertEqual(actual, expected)

    @patch('seaice.data.api.functools.partial')
    @patch('seaice.nasateam.invalid_ice_mask')
    def test_drop_invalid_ice_with_normal_params(self,
                                                 mock_invalid_ice_mask,
                                                 mock_partial):
        hemisphere = nt.NORTH

        mask = np.ones((448, 304), dtype=bool)
        mock_invalid_ice_mask.return_value = mask

        def wrapped_func():
            pass
        mock_partial.return_value = wrapped_func

        actual_filters = api._filters(hemisphere=hemisphere,
                                      month=1,
                                      drop_invalid_ice=True)

        expected_filters = [wrapped_func]

        actual_partial_called_with_func = mock_partial.call_args[0][0]
        actual_partial_called_with_mask = mock_partial.call_args[0][1]

        mock_invalid_ice_mask.assert_called_once_with(hemisphere, 1)
        self.assertEqual(actual_partial_called_with_func, gf.drop_invalid_ice)
        npt.assert_array_equal(mask, actual_partial_called_with_mask)
        self.assertEqual(actual_filters, expected_filters)

    @patch('seaice.data.api.functools.partial')
    @patch('seaice.data.api._invalid_ice_mask_for_median')
    def test_drop_invalid_ice_with_median_params(self,
                                                 mock_invalid_ice_mask_for_median,
                                                 mock_partial):
        hemisphere = nt.NORTH

        mask = np.ones((448, 304), dtype=bool)
        mock_invalid_ice_mask_for_median.return_value = mask

        def wrapped_func():
            pass
        mock_partial.return_value = wrapped_func

        actual_filters = api._filters(hemisphere=hemisphere,
                                      start_year=2001,
                                      end_year=2005,
                                      dayofyear=60,
                                      drop_invalid_ice=True)

        expected_filters = [wrapped_func]

        actual_partial_called_with_func = mock_partial.call_args[0][0]
        actual_partial_called_with_mask = mock_partial.call_args[0][1]

        mock_invalid_ice_mask_for_median.assert_called_once_with(2001, 2005, 60, hemisphere)
        self.assertEqual(actual_partial_called_with_func, gf.drop_invalid_ice)
        npt.assert_array_equal(mask, actual_partial_called_with_mask)
        self.assertEqual(actual_filters, expected_filters)

    def test_prevent_empty(self):
        actual = api._filters(allow_empty_gridset=False)
        expected = [gf.prevent_empty]
        self.assertEqual(actual, expected)

    @patch('seaice.nasateam.invalid_ice_mask')
    @patch('seaice.data.api._invalid_ice_mask_for_median')
    def test_order_prevent_empty_is_last(self,
                                         mock_invalid_ice_mask,
                                         mock__invalid_ice_mask_for_median):
        mask = np.ones((448, 304), dtype=bool)
        mock_invalid_ice_mask.return_value = mask
        mock__invalid_ice_mask_for_median.return_value = mask

        ALLOW_EMPTY_GRIDSET = False

        for drop_land in [True, False, None]:
            for allow_bad_dates in [True, False, None]:
                for interpolation_radius in [0, 1]:
                    for drop_invalid_ice in [True, False, None]:
                        for hemisphere, month, start_year, end_year, dayofyear in [
                                (nt.NORTH, 1, None, None, None),
                                (nt.NORTH, None, 2000, 2005, 60),
                                (None, None, None, None, None)]:
                            actual_filters = api._filters(
                                hemisphere=hemisphere,
                                month=month,
                                drop_land=drop_land,
                                allow_bad_dates=allow_bad_dates,
                                interpolation_radius=interpolation_radius,
                                drop_invalid_ice=drop_invalid_ice,

                                allow_empty_gridset=ALLOW_EMPTY_GRIDSET)

                            actual_prevent_empty_index = actual_filters.index(gf.prevent_empty)
                            expected_prevent_empty_index = len(actual_filters) - 1

                            self.assertEqual(actual_prevent_empty_index,
                                             expected_prevent_empty_index)

    @patch('seaice.nasateam.invalid_ice_mask')
    @patch('seaice.data.api._invalid_ice_mask_for_median')
    def test_order_drop_bad_dates_before_interpolate(self,
                                                     mock_invalid_ice_mask,
                                                     mock__invalid_ice_mask_for_median):
        mask = np.ones((448, 304), dtype=bool)
        mock_invalid_ice_mask.return_value = mask
        mock__invalid_ice_mask_for_median.return_value = mask

        ALLOW_BAD_DATES = False
        INTERPOLATION_RADIUS = 1

        for drop_land in [True, False, None]:
            for drop_invalid_ice in [True, False, None]:
                for hemisphere, month, start_year, end_year, dayofyear in [
                        (nt.NORTH, 1, None, None, None),
                        (nt.NORTH, None, 2000, 2005, 60),
                        (None, None, None, None, None)]:
                    for allow_empty_gridset in [True, False, None]:
                        actual_filters = api._filters(
                            hemisphere=hemisphere,
                            month=month,
                            drop_land=drop_land,
                            drop_invalid_ice=drop_invalid_ice,
                            allow_empty_gridset=allow_empty_gridset,

                            allow_bad_dates=ALLOW_BAD_DATES,
                            interpolation_radius=INTERPOLATION_RADIUS)

                        drop_bad_dates_index = actual_filters.index(gf.drop_bad_dates)
                        interpolate_index = actual_filters.index(gf.interpolate)

                        self.assertLess(drop_bad_dates_index, interpolate_index)


class Test__anomaly_gridset(unittest.TestCase):
    pole_hole_value = 251

    def _metadata(self):
        flags = {'pole': self.pole_hole_value}

        return {
            'valid_data_range': (0, 100),
            'files': [],
            'period_index': pd.PeriodIndex([], freq='M'),
            'flags': flags
        }

    def _climatology_gridset(self, *data):
        return {'data': np.dstack(data), 'metadata': self._metadata()}

    def _month_gridset(self, data):
        return {'data': data, 'metadata': self._metadata()}

    def test_subtract_average_climatology_from_month(self):
        month_gridset = self._month_gridset(
            np.array([[25, 25],
                      [25, 25]]))
        climatology_gridset = self._climatology_gridset(
            np.array([[17, 15],
                      [18, 22]]),
            np.array([[19, 25],
                      [20, 16]]))

        actual = api._anomaly_gridset(month_gridset, climatology_gridset)

        expected = np.array([[25 - 18, 25 - 20],
                             [25 - 19, 25 - 19]])
        npt.assert_array_equal(actual['data'], expected)

    def test_preserves_values_outside_valid_range_from_climatology(self):
        month_gridset = self._month_gridset(
            np.array([[25, 10],
                      [25, 10]]))
        climatology_gridset = self._climatology_gridset(
            np.array([[17, 101],
                      [17, 101]]),
            np.array([[19, 101],
                      [19, 101]]))

        actual = api._anomaly_gridset(month_gridset, climatology_gridset)

        expected = np.array([[7, 101],
                             [7, 101]])
        npt.assert_array_equal(actual['data'], expected)

    def test_preserves_largest_pole_hole_month_gridset(self):
        """Tests that the largest pole hole is retained from the
        month_gridset.
        """
        month_gridset = self._month_gridset(
            np.array([[self.pole_hole_value, 25],
                      [self.pole_hole_value, self.pole_hole_value]]))
        climatology_gridset = self._climatology_gridset(
            np.array([[17, 15],
                      [self.pole_hole_value, self.pole_hole_value]]),
            np.array([[19, 25],
                      [self.pole_hole_value, self.pole_hole_value]]))

        actual = api._anomaly_gridset(month_gridset, climatology_gridset)

        expected = np.array([[self.pole_hole_value, 25 - 20],
                             [self.pole_hole_value, self.pole_hole_value]])
        npt.assert_array_equal(actual['data'], expected)

    def test_preserves_largest_pole_hole_climatology_gridset(self):
        """Tests that the largest pole hole is retained from the
        climatology_gridset.
        """
        month_gridset = self._month_gridset(
            np.array([[25, 25],
                      [self.pole_hole_value, self.pole_hole_value]]))
        climatology_gridset = self._climatology_gridset(
            np.array([[17, self.pole_hole_value],
                      [self.pole_hole_value, self.pole_hole_value]]),
            np.array([[19, self.pole_hole_value],
                      [self.pole_hole_value, self.pole_hole_value]]))

        actual = api._anomaly_gridset(month_gridset, climatology_gridset)

        expected = np.array([[25 - 18, self.pole_hole_value],
                             [self.pole_hole_value, self.pole_hole_value]])
        npt.assert_array_equal(actual['data'], expected)
