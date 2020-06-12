from unittest.mock import patch
import unittest

from nose.tools import assert_equals
import datetime as dt
import numpy as np
import pandas as pd

import seaice.data.locator as locator
import seaice.nasateam as nt


class Test_all_daily_file_paths_for_month(unittest.TestCase):

    @patch('seaice.data.locator.daily_file_paths_in_date_range')
    def test_all_daily_file_paths_for_month(self, mock_daily_file_paths_in_date_range):
        hemisphere = nt.NORTH
        year = 2015
        month = 2
        search_paths = ['empty']

        locator.all_daily_file_paths_for_month(hemisphere, year, month, search_paths)

        locator.daily_file_paths_in_date_range.assert_called_once_with(
            hemisphere,
            dt.date(2015, 2, 1),
            dt.date(2015, 2, 28),
            search_paths
        )

    @patch('seaice.data.locator.daily_file_paths_in_date_range')
    def test_all_daily_file_paths_for_month_leap_year(self, mock_daily_file_paths_in_date_range):
        hemisphere = nt.NORTH
        year = 2012
        month = 2
        search_paths = ['empty']

        locator.all_daily_file_paths_for_month(hemisphere, year, month, search_paths)

        locator.daily_file_paths_in_date_range.assert_called_once_with(
            hemisphere,
            dt.date(2012, 2, 1),
            dt.date(2012, 2, 29),
            search_paths
        )


class Test_daily_file_path(unittest.TestCase):

    @patch('seaice.data.locator._daily_file_paths_in_period_index')
    def test_daily_file_path(self, mock_daily_file_paths_in_date_range):
        hemisphere = nt.NORTH
        period_index = pd.period_range('2012-09-16', '2012-09-16', freq='D')
        search_paths = ['empty']

        locator.daily_file_path(hemisphere, period_index, search_paths)

        locator._daily_file_paths_in_period_index.assert_called_once_with(
            hemisphere,
            period_index,
            search_paths
        )

    @patch('seaice.data.locator._daily_file_paths_in_period_index')
    def test_daily_file_path_with_interpolation(self, mock_daily_file_paths_in_date_range):
        hemisphere = nt.NORTH
        period_index = pd.period_range('2012-09-15', '2012-09-17', freq='D')
        search_paths = ['empty']

        locator.daily_file_path(hemisphere, period_index, search_paths)

        locator._daily_file_paths_in_period_index.assert_called_once_with(
            hemisphere,
            period_index,
            search_paths
        )


class Test_monthly_file_path(unittest.TestCase):

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_monthly_file_path(self, mock__find_all_nasateam_ice_files):
        locator._find_all_nasateam_ice_files.return_value = ['/anyroot/nt_201209_f17_v1.1_s.bin',
                                                             '/anyroot/nt_201210_f17_v1.1_s.bin',
                                                             '/anyroot/nt_201211_f17_v1.1_s.bin']

        hemisphere = nt.SOUTH
        year = 2012
        month = 9
        search_paths = ['empty']

        actual = locator.monthly_file_path(hemisphere, year, month, search_paths)
        expected = '/anyroot/nt_201209_f17_v1.1_s.bin'

        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_monthly_file_path_returns_None_if_missing(self, mock__find_all_nasateam_ice_files):
        locator._find_all_nasateam_ice_files.return_value = [
            '/anyroot/nt_201209_f17_v1.1_s.bin',
            '/anyroot/nt_201210_f13_v1.1_s.bin',
            '/anyroot/nt_201211_f17_v1.1_s.bin'
        ]

        hemisphere = nt.SOUTH
        year = 2013
        month = 10
        search_paths = ['empty']

        actual = locator.monthly_file_path(hemisphere, year, month, search_paths)
        expected = None

        assert_equals(expected, actual)


class Test_daily_file_paths_in_date_range(unittest.TestCase):

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_daily_file_paths_in_date_range(self, mock__find_all_nasateam_ice_files):
        search_paths = ['empty']
        expected = ['/anyroot/nt_20120918_f17_v1.1_s.bin']

        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20120918_f17_v1.1_s.bin',
                                                          '/anyroot/nt_20120919_f13_v1.1_s.bin',
                                                          '/anyroot/nt_20120920_f17_v1.1_s.bin']

        date = dt.date(2012, 9, 18)
        hemisphere = nt.SOUTH

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, search_paths)

        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_daily_file_paths_in_date_range_nrt(self, mock__find_all_nasateam_ice_files):
        search_paths = ['empty']
        expected = ['/anyroot/nt_20150901_f17_nrt_n.bin']

        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20120919_f17_nrt_s.bin',
                                                          '/anyroot/nt_20150901_f17_nrt_n.bin',
                                                          '/anyroot/nt_20150901_f17_nrt_s.bin',
                                                          '/anyroot/nt_20120920_f17_nrt_s.bin']

        date = dt.date(2015, 9, 1)
        hemisphere = nt.NORTH

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, search_paths)

        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_daily_file_paths_in_date_range_with_interpolation(self,
                                                               mock__find_all_nasateam_ice_files):
        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20120919_f17_nrt_n.bin',
                                                          '/anyroot/nt_20120920_f17_nrt_n.bin',
                                                          '/anyroot/nt_20120921_f17_nrt_n.bin']
        expected = [
            '/anyroot/nt_20120919_f17_nrt_n.bin',
            '/anyroot/nt_20120920_f17_nrt_n.bin',
            '/anyroot/nt_20120921_f17_nrt_n.bin']

        actual = locator.daily_file_paths_in_date_range(
            nt.NORTH,
            dt.date(2012, 9, 19),
            dt.date(2012, 9, 21),
            ['search_path']
        )

        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_filter_correct_platforms_when_preferred_platform_exists(
            self,
            mock__find_all_nasateam_ice_files
    ):
        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20071230_f13_v01_s.bin',
                                                          '/anyroot/nt_20071230_f17_v01_s.bin',
                                                          '/anyroot/nt_20071231_f13_v01_s.bin',
                                                          '/anyroot/nt_20071231_f17_v01_s.bin']

        date = dt.date(2007, 12, 31)
        hemisphere = nt.SOUTH
        expected = ['/anyroot/nt_20071231_f13_v01_s.bin']

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, ['search_path'])
        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_filter_out_platforms_when_only_platform_outside_platform_range(
            self,
            mock__find_all_nasateam_ice_files
    ):

        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20071231_f17_v01_s.bin']

        date = dt.date(2007, 12, 31)
        hemisphere = nt.SOUTH
        expected = []

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, ['search_path'])
        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_filter_correct_platforms_when_only_preferred_platform_exists(
            self,
            mock__find_all_nasateam_ice_files
    ):

        mock__find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20071231_f13_v01_s.bin']

        date = dt.date(2007, 12, 31)
        hemisphere = nt.SOUTH
        expected = ['/anyroot/nt_20071231_f13_v01_s.bin']

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, ['search_path'])
        assert_equals(expected, actual)

    @patch('seaice.data.locator._find_all_nasateam_ice_files')
    def test_daily_file_paths_in_date_range_uses_final(self, mock__find_all_nasateam_ice_files):
        locator._find_all_nasateam_ice_files.return_value = ['/anyroot/nt_20071231_f13_nrt_s.bin',
                                                             '/anyroot/nt_20071231_f13_v01_s.bin']

        date = dt.date(2007, 12, 31)
        hemisphere = nt.SOUTH
        expected = ['/anyroot/nt_20071231_f13_v01_s.bin']

        actual = locator.daily_file_paths_in_date_range(hemisphere, date, date, ['empty'])
        assert_equals(expected, actual)


class Test__filter_by_preferred_platform_dates(unittest.TestCase):

    def test_filter_correct_platforms_monthly(self):
        data_frame = locator._get_monthly_filename_data_frame(('nt_200701_f13_v01_n.bin',
                                                               'nt_200701_f17_v01_n.bin',
                                                               'nt_200702_f13_v01_n.bin',
                                                               'nt_200702_f17_v01_n.bin',
                                                               'nt_200703_f13_v01_n.bin',
                                                               'nt_200703_f17_v01_n.bin',
                                                               'nt_200704_f13_v01_n.bin',
                                                               'nt_200704_f17_v01_n.bin',
                                                               'nt_200705_f13_v01_n.bin',
                                                               'nt_200705_f17_v01_n.bin',
                                                               'nt_200706_f13_v01_n.bin',
                                                               'nt_200706_f17_v01_n.bin',
                                                               'nt_200707_f13_v01_n.bin',
                                                               'nt_200707_f17_v01_n.bin',
                                                               'nt_200708_f13_v01_n.bin',
                                                               'nt_200708_f17_v01_n.bin',
                                                               'nt_200709_f13_v01_n.bin',
                                                               'nt_200709_f17_v01_n.bin',
                                                               'nt_200710_f13_v01_n.bin',
                                                               'nt_200710_f17_v01_n.bin',
                                                               'nt_200711_f13_v01_n.bin',
                                                               'nt_200711_f17_v01_n.bin',
                                                               'nt_200712_f13_v01_n.bin',
                                                               'nt_200712_f17_v01_n.bin'), 'N')

        expected = sorted(['nt_200701_f13_v01_n.bin',
                           'nt_200702_f13_v01_n.bin',
                           'nt_200703_f13_v01_n.bin',
                           'nt_200704_f13_v01_n.bin',
                           'nt_200705_f13_v01_n.bin',
                           'nt_200706_f13_v01_n.bin',
                           'nt_200707_f13_v01_n.bin',
                           'nt_200708_f13_v01_n.bin',
                           'nt_200709_f13_v01_n.bin',
                           'nt_200710_f13_v01_n.bin',
                           'nt_200711_f13_v01_n.bin',
                           'nt_200712_f13_v01_n.bin'])

        actual = sorted(list(locator._filter_by_preferred_platform_dates(data_frame).filename))

        np.testing.assert_array_equal(expected, actual)

    def test_filter_correct_platforms_daily_n(self):

        data_frame = locator._get_daily_filename_data_frame(('nt_20071228_f13_v01_n.bin',
                                                             'nt_20071228_f17_v01_n.bin',

                                                             'nt_20071229_f17_v01_n.bin',
                                                             'nt_20071229_f13_v01_n.bin',
                                                             'nt_20071229_f13_v01_s.bin',
                                                             'nt_20071229_f17_v01_s.bin',

                                                             'nt_20071230_f13_v01_n.bin',
                                                             'nt_20071230_f13_v01_s.bin',

                                                             'nt_20071231_f13_v01_n.bin',
                                                             'nt_20071231_f17_v01_n.bin',
                                                             'nt_20071231_f13_v01_s.bin',
                                                             'nt_20071231_f17_v01_s.bin'), 'N')

        expected = sorted(['nt_20071228_f13_v01_n.bin',
                           'nt_20071229_f13_v01_n.bin',
                           'nt_20071230_f13_v01_n.bin',
                           'nt_20071231_f13_v01_n.bin'])

        actual = sorted(list(locator._filter_by_preferred_platform_dates(data_frame).filename))

        np.testing.assert_array_equal(expected, actual)

    def test_filter_correct_platforms_daily_s(self):

        data_frame = locator._get_daily_filename_data_frame(('nt_20071228_f13_v01_n.bin',
                                                             'nt_20071228_f17_v01_n.bin',

                                                             'nt_20071229_f17_v01_n.bin',
                                                             'nt_20071229_f13_v01_n.bin',
                                                             'nt_20071229_f13_v01_s.bin',
                                                             'nt_20071229_f17_v01_s.bin',

                                                             'nt_20071230_f13_v01_n.bin',
                                                             'nt_20071230_f13_v01_s.bin',

                                                             'nt_20071231_f13_v01_n.bin',
                                                             'nt_20071231_f17_v01_n.bin',
                                                             'nt_20071231_f13_v01_s.bin',
                                                             'nt_20071231_f17_v01_s.bin'), 'S')

        expected = sorted(['nt_20071229_f13_v01_s.bin',
                           'nt_20071230_f13_v01_s.bin',
                           'nt_20071231_f13_v01_s.bin'])

        actual = sorted(list(locator._filter_by_preferred_platform_dates(data_frame).filename))

        np.testing.assert_array_equal(expected, actual)

    def test_filter_correct_platforms_when_one_platform_is_unkown(self):

        data_frame = locator._get_daily_filename_data_frame(('nt_20071228_f00_v01_n.bin',
                                                             'nt_20071228_f13_v01_n.bin'), 'N')

        expected = sorted(['nt_20071228_f13_v01_n.bin'])

        actual = sorted(list(locator._filter_by_preferred_platform_dates(data_frame).filename))

        np.testing.assert_array_equal(expected, actual)

    def test_filter_does_not_use_unkown_platform_when_only_choice(self):

        data_frame = locator._get_daily_filename_data_frame(('nt_20071228_f00_v01_n.bin',), 'N')

        expected = sorted([])

        actual = sorted(list(locator._filter_by_preferred_platform_dates(data_frame).filename))

        np.testing.assert_array_equal(expected, actual)


class Test__filter_overlapping_nrt_and_final(unittest.TestCase):

    def test__filter_overlapping_nrt_and_final(self):
        expected = ['/anyroot/nt_20150901_f17_v01_n.bin']
        overlapping_files = ['/anyroot/nt_20150901_f17_v01_n.bin',
                             '/anyroot/nt_20150901_f17_nrt_n.bin']

        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    def test__filter_overlapping_nrt_and_final_with_no_nrt(self):
        expected = ['/anyroot/nt_20150901_f17_v01_n.bin']
        overlapping_files = ['/anyroot/nt_20150901_f17_v01_n.bin']

        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    def test__filter_overlapping_nrt_and_final_when_keeping_nrt(self):
        expected = ['/anyroot/nt_20150901_f17_nrt_n.bin']
        overlapping_files = ['/anyroot/nt_20150901_f17_nrt_n.bin']

        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    def test__filter_overlapping_nrt_and_final_with_empty_set(self):
        expected = []
        overlapping_files = []

        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', dt.date(2016, 2, 13))
    def test_with_overlapping_around_final_data_cutoff(self):
        overlapping_files = ['/anyroot/nt_20160213_f17_v01_n.bin',
                             '/anyroot/nt_20160213_f17_nrt_n.bin',
                             '/anyroot/nt_20160214_f17_v01_n.bin',
                             '/anyroot/nt_20160214_f17_nrt_n.bin']

        expected = ['/anyroot/nt_20160213_f17_v01_n.bin',
                    '/anyroot/nt_20160214_f17_nrt_n.bin']
        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', dt.date(2016, 2, 13))
    def test_with_only_final_around_final_data_cutoff(self):
        overlapping_files = ['/anyroot/nt_20160213_f17_v01_n.bin',
                             '/anyroot/nt_20160214_f17_v01_n.bin']

        expected = ['/anyroot/nt_20160213_f17_v01_n.bin']
        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', dt.date(2016, 2, 13))
    def test_with_only_nrt_around_final_data_cutoff(self):
        overlapping_files = ['/anyroot/nt_20160213_f17_nrt_n.bin',
                             '/anyroot/nt_20160214_f17_nrt_n.bin']

        expected = ['/anyroot/nt_20160213_f17_nrt_n.bin',
                    '/anyroot/nt_20160214_f17_nrt_n.bin']
        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', dt.date(2016, 2, 13))
    def test_with_final_almost_up_to_cutoff_and_nrt_data(self):
        overlapping_files = ['/anyroot/nt_20160212_f17_v01_n.bin',
                             '/anyroot/nt_20160213_f17_nrt_n.bin',
                             '/anyroot/nt_20160214_f17_nrt_n.bin']

        expected = ['/anyroot/nt_20160212_f17_v01_n.bin',
                    '/anyroot/nt_20160213_f17_nrt_n.bin',
                    '/anyroot/nt_20160214_f17_nrt_n.bin']
        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)

    @patch('seaice.nasateam.LAST_DAY_WITH_VALID_FINAL_DATA', dt.date(2016, 2, 13))
    def test_with_only_final_data_available_on_date_after_cutoff(self):
        overlapping_files = ['/anyroot/nt_20160212_f17_v01_n.bin',
                             '/anyroot/nt_20160213_f17_v01_n.bin',
                             '/anyroot/nt_20160214_f17_v01_n.bin',
                             '/anyroot/nt_20160215_f17_nrt_n.bin']

        expected = ['/anyroot/nt_20160212_f17_v01_n.bin',
                    '/anyroot/nt_20160213_f17_v01_n.bin',
                    '/anyroot/nt_20160215_f17_nrt_n.bin']
        actual = locator._filter_overlapping_nrt_and_final(overlapping_files)

        assert_equals(expected, actual)


class Test__find_all_nasateam_ice_files(unittest.TestCase):

    @patch('seaice.data.locator.os.walk')
    def test__find_all_nasateam_ice_files(self, mock_walk):

        files = ['/anyroot/nt_20120918_f17_v1.1_s.bin',
                 '/anyroot/stupid/not/really/a/s.bin',
                 '/anyroot/stupid/not/really/a/nt_20120919_f13_v1.1_s.png',
                 '/anyroot/nt_20120919_f13_v1.1_s.bin',
                 '/anyroot/nt_20120920_f17_v1.1_s.bin']

        mock_walk.return_value = [('', [], files)]

        expected = ['/anyroot/nt_20120918_f17_v1.1_s.bin',
                    '/anyroot/nt_20120919_f13_v1.1_s.bin',
                    '/anyroot/nt_20120920_f17_v1.1_s.bin']

        actual = locator._find_all_nasateam_ice_files('/who/cares/without/cache')

        assert_equals(expected, actual)


class Test__get_daily_filename_data_frame(unittest.TestCase):

    def test__get_daily_filename_data_frame(self):
        expected_columns = ['filename', 'date', 'year', 'month', 'day', 'platform', 'version',
                            'hemisphere']
        expected_length = 3
        expected_first_index = '2012-09-19'

        actual_frame = locator._get_daily_filename_data_frame((
            '/anyroot/nt_20120919_f17_nrt_n.bin',
            '/anyroot/nt_20120920_f17_nrt_n.bin',
            '/anyroot/nt_20120921_f17_nrt_n.bin'), 'N')

        assert_equals(len(actual_frame), expected_length)
        assert_equals(list(actual_frame.columns), expected_columns)
        assert_equals(str(actual_frame.index[0]), expected_first_index)


class Test__get_monthly_filename_data_frame(unittest.TestCase):

    def test__get_monthly_filename_data_frame(self):
        expected_columns = ['filename', 'date', 'year', 'month', 'platform',
                            'version', 'hemisphere']

        expected_length = 3
        expected_first_index = '2012-08'

        actual_frame = locator._get_monthly_filename_data_frame((
            '/anyroot/nt_201208_f17_nrt_n.bin',
            '/anyroot/nt_201209_f17_nrt_n.bin',
            '/anyroot/nt_201210_f17_nrt_n.bin'), 'N')

        assert_equals(len(actual_frame), expected_length)
        assert_equals(list(actual_frame.columns), expected_columns)
        assert_equals(str(actual_frame.index[0]), expected_first_index)
