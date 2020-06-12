import datetime as dt
from functools import wraps
from unittest import TestCase
from unittest.mock import patch

import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal
from pandas.util.testing import assert_series_equal

import seaice.nasateam as nt
import seaice.sedna.sedna as sedna
from seaice.sedna.cube import ConcentrationCube as Cube


TestCase.maxDiff = None

TODAY_PERIOD = pd.Period(dt.date.today(), 'D')


class mock_today(object):
    def __init__(self, year, month, day):
        self.date = dt.date(year, month, day)

    def __call__(self, func):
        @wraps(func)
        def func_wrapper(*args):
            with patch('seaice.sedna.sedna.dt_date') as mock_date:
                mock_date.today.return_value = self.date
                mock_date.side_effect = lambda *args_, **kw: dt.date(*args_, **kw)
                return func(*args)
        return func_wrapper


class Test__poly_fit_delta(TestCase):

    def _add_index(self, series):
        index = pd.period_range(start=dt.date(2001, 1, 1), periods=len(series), freq='D')
        series.index = index
        return series

    def test_valid_data(self):
        s = self._add_index(pd.Series([0, 1, 2, 3, 4]))
        actual = sedna._poly_fit_delta(s)
        expected = 0
        self.assertAlmostEqual(expected, actual)

    def test_delta(self):
        s = self._add_index(pd.Series([0, 5, 10, 15, 15]))
        expected = -5
        actual = sedna._poly_fit_delta(s)
        self.assertAlmostEqual(expected, actual)

    def test_interpolate_missing_correctly(self):
        s = self._add_index(pd.Series([0, 1, 2, np.nan, np.nan, 5.1]))
        actual = sedna._poly_fit_delta(s)
        expected = .1
        self.assertAlmostEqual(expected, actual, delta=.00001)

    def test_interpolate_missing_beginning(self):
        s = self._add_index(pd.Series([np.nan, np.nan, 3, 4, 5, 6, 7.5]))
        actual = sedna._poly_fit_delta(s)
        expected = .5
        self.assertAlmostEqual(expected, actual, delta=.00001)

    def test_missing_target_returns_nan(self):
        s = self._add_index(pd.Series([1, 2, 3, 4, 5, 6, np.nan, np.nan]))
        actual = sedna._poly_fit_delta(s)
        self.assertTrue(np.isnan(actual))

    def test_huge_delta(self):
        s = self._add_index(pd.Series([1, 2, 3, np.nan, np.nan, 60]))
        expected = 54
        actual = sedna._poly_fit_delta(s)
        self.assertAlmostEqual(expected, actual)


class Test__set_failed_qa_flag(TestCase):
    eval_days = 3
    regression_delta_km2 = 1

    def _generate_expected_series(self, index, expected_values):
        return pd.Series(expected_values, index, name='failed_qa')

    def _set_up_input_frame(self, extents):
        test_index = pd.period_range(start='2015-01-01', periods=len(extents), freq='D')
        test_frame = pd.DataFrame(data={'total_extent_km2': extents,
                                        'failed_qa': [''] * len(extents),
                                        'filename': [['foo']] * len(extents)},
                                  index=test_index)
        return test_frame

    def test_set_failed_qa_flag_if_file_blank(self):
        extents_length = 5
        test_frame = self._set_up_input_frame(np.arange(extents_length))
        test_frame['filename'] = [[]] * extents_length
        frame = sedna._set_failed_qa_flag(test_frame, self.eval_days, self.regression_delta_km2)
        expected_values = ['', '', '', False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_valid_data(self):

        test_frame = self._set_up_input_frame(np.arange(11))
        frame = sedna._set_failed_qa_flag(test_frame, self.eval_days, self.regression_delta_km2)

        expected_values = ['', '', '', False, False, False, False, False, False, False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_missing_data_marked(self):
        test_frame = self._set_up_input_frame([0, 1, 2, 3, np.nan, np.nan, 6, 7, 8, 9, 10])
        frame = sedna._set_failed_qa_flag(test_frame, self.eval_days, self.regression_delta_km2)

        expected_values = ['', '', '', False, True, True, '', '', False, False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_missing_data_spike(self):
        eval_days = 5
        test_frame = self._set_up_input_frame([1, 2, 3, np.nan, np.nan, 60, 7, 8, 9, 10])
        frame = sedna._set_failed_qa_flag(test_frame, eval_days, self.regression_delta_km2)

        expected_values = ['', '', '', '', '', True, False, False, False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_missing_data_with_bad_trailing_data(self):
        test_frame = self._set_up_input_frame([1, 2, 3, np.nan, np.nan, 1000, 10000])
        frame = sedna._set_failed_qa_flag(test_frame, self.eval_days, self.regression_delta_km2)

        expected_values = ['', '', '', True, True, '', '']
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_mixed_data(self):
        test_frame = self._set_up_input_frame([1, 2, 3, 4, 5, 6, 100, -50, 9, 10])
        frame = sedna._set_failed_qa_flag(test_frame, 4, self.regression_delta_km2)

        expected_values = ['', '', '', '', False, False, True, True, False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)

    def test_missing_initial_data(self):
        test_frame = self._set_up_input_frame([np.nan, np.nan, 3, 4, 5, 6, 7])
        frame = sedna._set_failed_qa_flag(test_frame, self.eval_days, self.regression_delta_km2)

        expected_values = ['', '', '', '', False, False, False]
        expected_series = self._generate_expected_series(frame.index, expected_values)
        assert_series_equal(frame['failed_qa'], expected_series)


class Test__create_row(TestCase):

    def test_works(self):
        period = pd.Period(dt.date(2010, 1, 4), 'D')
        extent = 13512223.12312
        area = 12305092.906
        missing = 626.5
        metadata = {'files': ['/nt_something_nrt_.bin', '/nt_something_else_nrt_.bin']}

        expected = {(period, 'N'): {'total_area_km2': 12305092.906,
                                    'total_extent_km2': 13512223.123,
                                    'filename': ['/nt_something_nrt_.bin',
                                                 '/nt_something_else_nrt_.bin'],
                                    'source_dataset': 'nsidc-0081',
                                    'missing_km2': 626.5,
                                    'failed_qa': False}}

        actual = sedna._create_row((period, 'N'), extent, area, missing, metadata,
                                   failed_qa=False)

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_area_km2'),
                                expected[(period, 'N')].pop('total_area_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_extent_km2'),
                                expected[(period, 'N')].pop('total_extent_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('missing_km2'),
                                expected[(period, 'N')].pop('missing_km2'))

        self.assertEqual(actual, expected)

    def test_works_with_monthly(self):
        period = pd.Period(dt.date(2010, 1, 4), 'M')
        extent = 13512223.12312
        area = 12305092.906
        missing = 626.5
        metadata = {'files': ['/nt_something_nrt_.bin', '/nt_something_else_nrt_.bin']}

        expected = {(period, 'N'): {'total_area_km2': 12305092.906,
                                    'total_extent_km2': 13512223.123,
                                    'filename': ['/nt_something_nrt_.bin',
                                                 '/nt_something_else_nrt_.bin'],
                                    'source_dataset': 'nsidc-0081',
                                    'missing_km2': 626.5}}

        actual = sedna._create_row((period, 'N'), extent, area, missing, metadata)

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_area_km2'),
                                expected[(period, 'N')].pop('total_area_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_extent_km2'),
                                expected[(period, 'N')].pop('total_extent_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('missing_km2'),
                                expected[(period, 'N')].pop('missing_km2'))

        self.assertEqual(actual, expected)

    def test_with_all_masked_extent(self):
        period = pd.Period(dt.date(2010, 1, 4), 'D')
        extent = np.ma.masked
        area = np.ma.masked
        missing = 75660222.409
        metadata = {'files': ['/nt_something_nrt_.bin', '/nt_something_nrt_else.bin']}

        expected = {(period, 'N'): {'total_area_km2': np.ma.masked,
                                    'total_extent_km2': np.ma.masked,
                                    'filename': ['/nt_something_nrt_.bin',
                                                 '/nt_something_nrt_else.bin'],
                                    'source_dataset': 'nsidc-0081',
                                    'missing_km2': 75660222.409,
                                    'failed_qa': False}}

        actual = sedna._create_row((period, 'N'), extent, area, missing, metadata,
                                   failed_qa=False)

        npt.assert_almost_equal(actual[(period, 'N')].pop('missing_km2'),
                                expected[(period, 'N')].pop('missing_km2'))

        self.assertEqual(actual, expected)

    def test_with_regional_stats(self):
        period = pd.Period(dt.date(2010, 1, 4), 'D')
        extent = 13512223.12312
        area = 12305092.906
        missing = 626.5
        metadata = {'files': ['/nt_something_nrt_.bin', '/nt_something_else_nrt_.bin']}

        regional_stats = [('Hudson', 20, 4, 1)]

        expected = {(period, 'N'): {'total_area_km2': 12305092.906,
                                    'total_extent_km2': 13512223.123,
                                    'filename': ['/nt_something_nrt_.bin',
                                                 '/nt_something_else_nrt_.bin'],
                                    'source_dataset': 'nsidc-0081',
                                    'missing_km2': 626.5,
                                    'Hudson_area_km2': 4,
                                    'Hudson_extent_km2': 20,
                                    'Hudson_missing_km2': 1,
                                    'failed_qa': False}}

        actual = sedna._create_row((period, 'N'), extent, area, missing, metadata,
                                   regional_stats, failed_qa=False)

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_area_km2'),
                                expected[(period, 'N')].pop('total_area_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('total_extent_km2'),
                                expected[(period, 'N')].pop('total_extent_km2'))

        npt.assert_almost_equal(actual[(period, 'N')].pop('missing_km2'),
                                expected[(period, 'N')].pop('missing_km2'))

        self.assertEqual(actual, expected)


class Test_daily_df_for_monthly_statistics(TestCase):

    def config(self, hemi):
        return {'hemisphere': {'short_name': hemi}}

    def _build_mock_frame(self):
        period_index = pd.period_range(start='1978-10-31', end='2017-06-12')
        count = len(period_index)

        df = pd.DataFrame({
            'date': list(period_index) * 2,
            'hemisphere': (['N'] * count) + (['S'] * count),
            'total_extent_km2': ([1] * count) + ([2] * count)
        })

        df = df.set_index(['date', 'hemisphere'])

        return df

    @mock_today(2017, 6, 13)
    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    def test_cuts_off_incomplete_months(self, mock__dataframe_from_data_store_daily):
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()

        actual = sedna._daily_df_for_monthly_statistics(self.config('N'))

        self.assertEqual(actual.index[0], pd.Period('1978-11-01', freq='D'))
        self.assertEqual(actual.index[-1], pd.Period('2017-05-31', freq='D'))

    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    def test_selects_hemisphere(self, mock__dataframe_from_data_store_daily):
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()

        actual = sedna._daily_df_for_monthly_statistics(self.config('N'))

        self.assertEqual(len(actual.hemisphere.unique()), 1)
        self.assertEqual(actual.hemisphere[0], 'N')

    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    def test_double_weights_smmr_days(self, mock__dataframe_from_data_store_daily):
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()

        actual = sedna._daily_df_for_monthly_statistics(self.config('N'))

        self.assertEqual(actual.index[0], pd.Period('1978-11-01', freq='D'))
        self.assertEqual(actual.index[1], pd.Period('1978-11-01', freq='D'))
        self.assertEqual(actual.index[6428], pd.Period('1987-08-20', freq='D'))
        self.assertEqual(actual.index[6429], pd.Period('1987-08-20', freq='D'))
        self.assertEqual(actual.index[6430], pd.Period('1987-08-21', freq='D'))
        self.assertEqual(actual.index[6431], pd.Period('1987-08-22', freq='D'))


class Test_update_sea_ice_statistics_daily(TestCase):
    def _build_mock_frame(self):
        df = pd.DataFrame({'failed_qa': np.array([], dtype=bool),
                           'total_extent_km2': np.array([], dtype=float)},
                          index=pd.PeriodIndex([], freq='D', name='date'),
                          columns=nt.DAILY_DEFAULT_COLUMNS)
        df = df.set_index([df.index, 'hemisphere'])
        return df

    def _mock_bad_sea_ice_statistics(self, gridset, period, config, failed_qa=False):
        row = {(period, 'N'): {
                                'total_area_km2': 500000,
                                'total_extent_km2': 500000,
                                'missing_km2': 0,
                                'filename': ['foo'],
                                'source_dataset': 'test-dataset',
                                'failed_qa': False}}

        if period == pd.Period('2015-02-02'):
            row[(period, 'N')]['total_extent_km2'] = 0
            return row
        else:
            return row

    def _get_config(self):
        config = {}
        config['hemisphere'] = nt.NORTH
        config['grid_areas'] = config['hemisphere']['grid_areas']
        config['search_paths'] = ['./test_data']
        config['interpolation_radius'] = 0
        config['regression_delta_km2'] = 1
        config['eval_days'] = 2
        config['extent_threshold'] = nt.EXTENT_THRESHOLD
        return config

    @patch('seaice.sedna.sedna._sea_ice_statistics')
    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    @patch('seaice.datastore.write_daily_datastore')
    def test_returns_false_on_failed_QA(self, mock_write_daily_datastore,
                                        mock__dataframe_from_data_store_daily,
                                        mock__sea_ice_statistics):
        config = self._get_config()
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()
        mock__sea_ice_statistics.side_effect = self._mock_bad_sea_ice_statistics
        dates = pd.period_range('2015-02-01', '2015-02-05')
        result = sedna.update_sea_ice_statistics_daily(dates, config, True)
        self.assertEqual(False, result)

    @patch('seaice.sedna.sedna._sea_ice_statistics')
    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    @patch('seaice.datastore.write_daily_datastore')
    def test_does_not_validate_if_flag_set(self, mock_write_daily_datastore,
                                           mock__dataframe_from_data_store_daily,
                                           mock__sea_ice_statistics):
        config = self._get_config()
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()
        mock__sea_ice_statistics.side_effect = self._mock_bad_sea_ice_statistics
        dates = pd.period_range('2015-02-01', '2015-02-05')
        result = sedna.update_sea_ice_statistics_daily(dates, config, False)
        self.assertEqual(True, result)


class Test__get_regional_stats(TestCase):

    @patch('numpy.fromfile')
    def test_works(self, mock_np_fromfile):
        concentration = np.array([[50., 2.],
                                  [255., 4.]])

        grid_areas = np.array([[4., 5.],
                               [6., 7.]])

        cube = Cube(concentration, grid_areas=grid_areas, missing_value=255)

        regional_masks = [{
            'file': '/foo/bar',
            'name': 'test',
            'hemisphere': 'north',
            'regions': {
                'bering': 3,
                'hudson': 4
            }
        }]

        # mock the parsed mask instead of actually reading the file
        mock_np_fromfile.return_value = np.array([[3., 0.],
                                                  [4., 4.]])

        hemisphere = {'long_name': 'north'}
        actual = sedna._get_regional_stats(cube, regional_masks, hemisphere, period=TODAY_PERIOD)

        expected = [('test_bering', 4.0, 2.0, 0), ('test_hudson', 7.0, 7 * .04, 6.0)]

        self.assertSetEqual(set(actual), set(expected))

    @patch('numpy.fromfile')
    def test_doesnt_calculate_regional_stats_when_wrong_hemisphere(self, mock_np_fromfile):
        concentration = np.array([[50., 2.],
                                  [255., 4.]])

        grid_areas = np.array([[4., 5.],
                               [6., 7.]])

        cube = Cube(concentration, grid_areas=grid_areas, missing_value=255)

        regional_masks = [{
            'file': '/foo/bar',
            'name': 'test',
            'hemisphere': 'north',
            'regions': {
                'bering': 3,
                'hudson': 4
            }
        }]

        # mock the parsed mask instead of actually reading the file
        mock_np_fromfile.return_value = np.array([[3., 0.],
                                                  [4., 4.]])

        hemisphere = {'long_name': 'south'}
        actual = sedna._get_regional_stats(cube, regional_masks, hemisphere, period=TODAY_PERIOD)

        expected = []

        self.assertListEqual(actual, expected)

    @patch('numpy.fromfile')
    def test_returns_0_when_region_is_covered_by_invalid_data_mask(self, mock_np_fromfile):
        period = TODAY_PERIOD

        concentration = np.array([[50., 2.],
                                  [255., 4.]])

        grid_areas = np.array([[4., 5.],
                               [6., 7.]])

        # the whole hudson region is in invalid ice
        invalid_data_mask = np.array([[False, False],
                                      [True, True]])

        cube = Cube(concentration,
                    grid_areas=grid_areas,
                    missing_value=255,
                    invalid_data_mask=invalid_data_mask)

        regional_masks = [{
            'file': '/foo/bar',
            'name': 'test',
            'hemisphere': 'north',
            'regions': {
                'bering': 3,
                'hudson': 4
            }
        }]

        # mock the parsed mask instead of actually reading the file
        mock_np_fromfile.return_value = np.array([[3., 0.],
                                                  [4., 4.]])

        hemisphere = {'long_name': 'north'}
        actual = sedna._get_regional_stats(cube, regional_masks, hemisphere, period)

        expected = [('test_bering', 4.0, 2.0, 0), ('test_hudson', 0, 0, 0)]

        self.assertSetEqual(set(actual), set(expected))

    @patch('numpy.fromfile')
    def test_returns_nans_when_region_is_covered_by_invalid_data_mask_and_whole_day_missing(
            self,
            mock_np_fromfile
    ):
        # a day in the SMMR period for which data is all `missing`
        period = pd.Period('1978-10-27', 'D')

        concentration = np.array([[255., 255.],
                                  [255., 255.]])

        grid_areas = np.array([[4., 5.],
                               [6., 7.]])

        # the whole hudson region is in invalid ice
        invalid_data_mask = np.array([[False, False],
                                      [True, True]])

        cube = Cube(concentration,
                    grid_areas=grid_areas,
                    missing_value=255,
                    invalid_data_mask=invalid_data_mask)

        regional_masks = [{
            'file': '/foo/bar',
            'name': 'test',
            'hemisphere': 'north',
            'regions': {
                'bering': 3,
                'hudson': 4
            }
        }]

        # mock the parsed mask instead of actually reading the file
        mock_np_fromfile.return_value = np.array([[3., 0.],
                                                  [4., 4.]])

        hemisphere = {'long_name': 'north'}
        actual = sorted(sedna._get_regional_stats(cube, regional_masks, hemisphere, period))

        expected = [('test_bering', np.nan, np.nan, 4.0), ('test_hudson', np.nan, np.nan, np.nan)]

        self.assertEqual(actual[0][0], expected[0][0])
        self.assertEqual(actual[1][0], expected[1][0])

        npt.assert_array_equal(actual[0][1:], expected[0][1:])
        npt.assert_array_equal(actual[1][1:], expected[1][1:])

    @patch('numpy.fromfile')
    def test_returns_nans_and_value_when_whole_day_missing(self, mock_np_fromfile):
        period = TODAY_PERIOD

        concentration = np.array([[255., 255.],
                                  [255., 255.]])

        grid_areas = np.array([[4., 5.],
                               [6., 7.]])

        invalid_data_mask = np.array([[False, False],
                                      [False, False]])

        cube = Cube(concentration,
                    grid_areas=grid_areas,
                    missing_value=255,
                    invalid_data_mask=invalid_data_mask)

        regional_masks = [{
            'file': '/foo/bar',
            'name': 'test',
            'hemisphere': 'north',
            'regions': {
                'bering': 3,
                'hudson': 4
            }
        }]

        # mock the parsed mask instead of actually reading the file
        mock_np_fromfile.return_value = np.array([[3., 0.],
                                                  [4., 4.]])

        hemisphere = {'long_name': 'north'}
        actual = sorted(sedna._get_regional_stats(cube, regional_masks, hemisphere, period))

        expected = [('test_bering', np.nan, np.nan, 4.0), ('test_hudson', np.nan, np.nan, 13.0)]

        self.assertEqual(actual[0][0], expected[0][0])
        self.assertEqual(actual[1][0], expected[1][0])

        npt.assert_array_equal(actual[0][1:], expected[0][1:])
        npt.assert_array_equal(actual[1][1:], expected[1][1:])


class Test__add_columns_to_dataframe(TestCase):
    def setUp(self):
        self.df = pd.DataFrame.from_dict({'evens': [2, 4, 6], 'odds': [3, 5, 7]}, orient='columns')
        self.df = self.df.set_index('evens')

    def test_works_with_empty_list(self):
        columns = []

        actual = sedna._add_columns_to_dataframe(self.df, columns)
        expected = self.df

        assert_frame_equal(actual, expected)

    def test_index_not_added_as_new_column(self):
        columns = ['evens']

        actual = sedna._add_columns_to_dataframe(self.df, columns)
        expected = self.df

        assert_frame_equal(actual, expected)

    def test_adds_new_column_with_default_fill_value(self):
        new_columns = ['new_column']

        actual = sedna._add_columns_to_dataframe(self.df, new_columns)

        d = {'evens': [2, 4, 6], 'odds': [3, 5, 7], 'new_column': [np.nan, np.nan, np.nan]}
        df = pd.DataFrame.from_dict(d, orient='columns')
        df = df.set_index('evens')
        expected = df

        # sort_index so the order of columns is the same in each dataframe
        assert_frame_equal(actual.sort_index(axis=1), expected.sort_index(axis=1))

    def test_adds_new_column_with_given_fill_value(self):
        columns = ['new_column']

        actual = sedna._add_columns_to_dataframe(self.df, columns, fill_value=2)

        d = {'evens': [2, 4, 6], 'odds': [3, 5, 7], 'new_column': [2, 2, 2]}
        df = pd.DataFrame.from_dict(d, orient='columns')
        df = df.set_index('evens')
        expected = df

        # sort_index so the order of columns is the same in each dataframe
        assert_frame_equal(actual.sort_index(axis=1), expected.sort_index(axis=1))

    def test_does_not_mutate_original_dataframe(self):
        original_df = self.df.copy()

        columns = ['new_column']

        sedna._add_columns_to_dataframe(self.df, columns, fill_value=2)

        assert_frame_equal(original_df, self.df)


class Test__source_dataset(TestCase):

    def test_near_real_time(self):
        filelist = ['nt_20150801_f17_nrt_s.bin']

        expected = 'nsidc-0081'

        actual = sedna._source_dataset(filelist)

        self.assertEqual(expected, actual)

    def test_final(self):
        filelist = ['nt_20150801_f17_v1.1_n.bin']

        expected = 'nsidc-0051'

        actual = sedna._source_dataset(filelist)

        self.assertEqual(expected, actual)

    def test_nrt_if_any_in_list_are(self):
        filelist = ['nt_20150801_f17_v1.1_n.bin',
                    'nt_20150802_f17_v1.1_n.bin',
                    'nt_20150803_f17_nrt_n.bin']

        expected = 'nsidc-0081'

        actual = sedna._source_dataset(filelist)

        self.assertEqual(expected, actual)

    def test_none_if_empty_list(self):
        filelist = []

        expected = None

        actual = sedna._source_dataset(filelist)

        self.assertEqual(expected, actual)


class Test__format_areal_value(TestCase):

    def test_rounds_to_3_digits(self):
        actual = sedna._format_areal_value(1.123456789)
        expected = 1.123

        npt.assert_equal(expected, actual)

    def test_rounds_to_3_digits_even(self):
        actual = sedna._format_areal_value(1.12450000)
        expected = 1.124

        npt.assert_equal(expected, actual)

    def test_nothing_to_round(self):
        actual = sedna._format_areal_value(100)
        expected = 100.0

        npt.assert_equal(expected, actual)

    def test_returns_masked_constant(self):
        actual = sedna._format_areal_value(np.ma.masked)
        expected = np.ma.masked

        self.assertIs(actual, expected)
