import datetime as dt
import unittest
from unittest.mock import patch

import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal, assert_series_equal, assert_index_equal

import seaice.timeseries.warp as warp
from seaice.timeseries.common import SeaIceTimeseriesInvalidArgument


class Test_filter_failed_qa(unittest.TestCase):
    def test_failed_qa_set_to_na(self):
        columns = ['Foo', 'Bar', 'failed_qa', 'filename']
        actual = pd.DataFrame([[1, 2, True, '/foo'], [1, 2, False, '/foo'], [1, 2, True, '/foo']],
                              columns=columns)
        expected = pd.DataFrame([[np.nan, np.nan, True, ''],
                                 [1, 2, False, '/foo'],
                                 [np.nan, np.nan, True, '']], columns=columns)
        actual = warp.filter_failed_qa(actual)
        assert_frame_equal(expected, actual)


class Test_climatologyMeans(unittest.TestCase):

    def test_means(self):
        index = pd.period_range(start='2000-05', end='2016-05', freq='12M')
        values = np.array([10,  20,  30,  40,  50,  50,  50,  50,  90,  99,
                           100, 100, 100, 100, 100, 100, 10])
        climatology_years = (2010, 2015)
        series = pd.Series(values, index=index)
        expected = pd.Series(100, index=[5])
        actual = warp.climatology_means(series, climatology_years)
        assert_series_equal(expected, actual)

    def test_multiple_months_in_series(self):
        anything = 3.14159
        index = pd.PeriodIndex(['2000-05', '2000-11', '2001-05', '2001-11', '2002-05', '2002-11',
                                '2003-05', '2003-11', '2004-05', '2004-11', '2005-05'],
                               freq='6M')
        climatology_years = (2000, 2001)
        values = [15., 99., 15., 99., anything, anything,
                  anything, anything, anything, anything, anything]
        series = pd.Series(values, index=index)

        actual = warp.climatology_means(series, climatology_years)

        expected = pd.Series([15., 99], index=[5, 11])
        assert_series_equal(expected, actual)


class TestFilterHemisphere(unittest.TestCase):
    def setUp(self):
        datetimes = pd.to_datetime(['1990-01-01', '1995-01-01', '2000-01-01', '2010-01-01'])
        daily_period_index = datetimes.to_period(freq='D')
        monthly_period_index = datetimes.to_period(freq='M')
        self.daily_df = pd.DataFrame({
            'hemisphere': ['S', 'N', 'S', 'N'],
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=daily_period_index)
        self.monthly_df = pd.DataFrame({
            'hemisphere': ['S', 'N', 'S', 'N'],
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=monthly_period_index)

    def test_daily_works_with_hemisphere(self):
        expected = self.daily_df.copy().ix[[0, 2]]
        actual = warp.filter_hemisphere(self.daily_df, 'S')
        assert_frame_equal(expected, actual)

    def test_daily_raises_error_with_none(self):
        with self.assertRaises(SeaIceTimeseriesInvalidArgument):
            warp.filter_hemisphere(self.daily_df, None)

    def test_monthly_works_with_hemisphere(self):
        expected = self.monthly_df.copy().ix[[1, 3]]
        actual = warp.filter_hemisphere(self.monthly_df, 'N')
        assert_frame_equal(expected, actual)

    def test_monthly_works_with_none(self):
        with self.assertRaises(SeaIceTimeseriesInvalidArgument):
            warp.filter_hemisphere(self.monthly_df, None)


class TestCollapseHemisphereFilter(unittest.TestCase):
    def test_frame_collapses(self):
        frame_length = 10
        index = pd.MultiIndex.from_tuples([('foo', 'N')]*frame_length, names=('date', 'hemisphere'))
        df = pd.DataFrame({'data': [5]*frame_length}, index=index)
        expected = df.reset_index(level='hemisphere', drop=False)
        actual = warp.collapse_hemisphere_index(df)
        assert_frame_equal(expected, actual)


class TestFilterBeforeAndFilterAfter(unittest.TestCase):

    def setUp(self):
        datetimes = pd.to_datetime(['1990-01-01', '1995-01-01', '2000-01-01', '2010-01-01'])
        daily_period_index = datetimes.to_period(freq='D')
        monthly_period_index = datetimes.to_period(freq='M')
        self.daily_df = pd.DataFrame({
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=daily_period_index)

        self.daily_df_with_datetimeindex = pd.DataFrame({
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=datetimes)

        self.monthly_df = pd.DataFrame({
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=monthly_period_index)

        self.monthly_df_with_datetimeindex = pd.DataFrame({
            'total_extent_km2': [19900000.0, 1995000.0, 2000000.0, 2010000.0],
            'total_area_km2': [1990.0, 1995.0, 2000.0, 2010.0]
        }, index=monthly_period_index.to_timestamp())

    def test_filter_before_works_with_daily_df_and_none(self):
        expected = self.daily_df.copy()
        actual = warp.filter_before(self.daily_df, None)
        assert_frame_equal(expected, actual)

    def test_filter_before_works_with_daily_df_and_none_and_DateTimeIndex(self):
        expected = self.daily_df_with_datetimeindex.copy()
        actual = warp.filter_before(self.daily_df_with_datetimeindex, None)
        assert_frame_equal(expected, actual)

    def test_filter_before_works_with_daily_df(self):
        expected = self.daily_df.copy().ix[1:]
        actual = warp.filter_before(self.daily_df, dt.datetime(1990, 5, 21))
        assert_frame_equal(expected, actual)

    def test_filter_before_works_with_monthly_df_and_none(self):
        expected = self.monthly_df.copy()
        actual = warp.filter_before(self.monthly_df, None)
        assert_frame_equal(expected, actual)

    def test_filter_before_works_with_monthly_df_and_none_and_DateTimeIndex(self):
        expected = self.monthly_df_with_datetimeindex.copy()
        actual = warp.filter_before(self.monthly_df_with_datetimeindex, None)
        assert_frame_equal(expected, actual)

    def test_filter_before_works_with_monthly_df(self):
        expected = self.monthly_df.copy().ix[1:]
        actual = warp.filter_before(self.monthly_df, dt.datetime(1990, 5, 21))
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_daily_df_and_none(self):
        expected = self.daily_df.copy()
        actual = warp.filter_after(self.daily_df, None)
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_daily_df_and_none_and_DateTimeIndex(self):
        expected = self.daily_df_with_datetimeindex.copy()
        actual = warp.filter_after(self.daily_df_with_datetimeindex, None)
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_daily_df(self):
        expected = self.daily_df.copy().ix[0:1]
        actual = warp.filter_after(self.daily_df, dt.datetime(1990, 5, 21))
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_monthly_df_and_none(self):
        expected = self.monthly_df.copy()
        actual = warp.filter_after(self.monthly_df, None)
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_monthly_df_and_none_and_DateTimeIndex(self):
        expected = self.monthly_df_with_datetimeindex.copy()
        actual = warp.filter_after(self.monthly_df_with_datetimeindex, None)
        assert_frame_equal(expected, actual)

    def test_filter_after_works_with_monthly_df(self):
        expected = self.monthly_df.copy().ix[0:1]
        actual = warp.filter_after(self.monthly_df, dt.datetime(1990, 5, 21))
        assert_frame_equal(expected, actual)


class TestInterpolateDf(unittest.TestCase):

    def setUp(self):
        datetimes = pd.date_range('1990-05-01', '1990-05-10', freq='D')
        self.extents = np.linspace(100000., 200000., num=len(datetimes))
        self.areas = np.linspace(70000., 180000., num=len(datetimes))
        missing_extents = self.extents.copy()
        missing_areas = self.areas.copy()
        missing_extents[2:4] = np.nan
        missing_areas[4:8] = np.nan
        self.daily_period_index = datetimes.to_period(freq='D')
        self.df = pd.DataFrame({
            'total_extent_km2': missing_extents,
            'total_area_km2': missing_areas,
        }, index=self.daily_period_index)

    def test_works_limit_one_multiple_missing(self):
        """Expect only first nan to be interpolated."""
        expected_extents = self.extents
        expected_extents[3] = np.nan
        expected_areas = self.areas
        expected_areas[5:8] = np.nan

        actual = warp.interpolate_df(self.df, 1)
        expected = pd.DataFrame({'total_extent_km2': expected_extents,
                                 'total_area_km2': expected_areas},
                                index=self.daily_period_index)
        expected = expected[expected.columns.sort_values()]
        assert_frame_equal(expected, actual)

    def test_works_limit_None_multiple_missing(self):
        """Expect all nans to be interpolated."""
        expected_extents = self.extents
        expected_areas = self.areas

        actual = warp.interpolate_df(self.df, None)
        expected = pd.DataFrame({'total_extent_km2': expected_extents,
                                 'total_area_km2': expected_areas},
                                index=self.daily_period_index)
        expected = expected[expected.columns.sort_values()]
        assert_frame_equal(expected, actual)

    def test_columns_argument(self):
        """expect only columns included"""
        expected_extents = self.extents
        expected_extents[3] = np.nan
        expected_areas = self.areas
        expected_areas[5:8] = np.nan

        actual = warp.interpolate_df(self.df, 1, columns=['total_area_km2'])
        expected = pd.DataFrame({'total_area_km2': expected_areas},
                                index=self.daily_period_index)
        expected = expected[expected.columns.sort_values()]
        assert_frame_equal(expected, actual)


class TestNDayAverage(unittest.TestCase):

    def setUp(self):
        datetimes = pd.date_range('1990-05-01', '1990-05-10', freq='D')
        self.extents = np.linspace(100000., 200000., num=len(datetimes))
        self.areas = np.linspace(70000., 180000., num=len(datetimes))
        missing_extents = self.extents.copy()
        missing_areas = self.areas.copy()
        missing_extents[2:4] = np.nan
        missing_areas[4:8] = np.nan
        self.daily_period_index = datetimes.to_period(freq='D')
        self.df = pd.DataFrame({
            'total_extent_km2': missing_extents,
            'total_area_km2': missing_areas,
        }, index=self.daily_period_index)

        #  What the setup df looks like:
        # >>> df
        #             total_area_km2  total_extent_km2
        # 1990-05-01    70000.000000     100000.000000
        # 1990-05-02    82222.222222     111111.111111
        # 1990-05-03    94444.444444               NaN
        # 1990-05-04   106666.666667               NaN
        # 1990-05-05             NaN     144444.444444
        # 1990-05-06             NaN     155555.555556
        # 1990-05-07             NaN     166666.666667
        # 1990-05-08             NaN     177777.777778
        # 1990-05-09   167777.777778     188888.888889
        # 1990-05-10   180000.000000     200000.000000

    def test_3day_window_1_min_valid_filter_missing(self):
        """Expect that extents are nday averaged properly with 3day window and 1 valid needed, with
           all values that were originally NaN still NaN"""
        in_areas = self.df.total_area_km2
        mean_areas = np.zeros_like(in_areas)
        mean_areas[0] = np.mean(in_areas[0:1])
        mean_areas[1] = np.mean(in_areas[0:2])
        mean_areas[2] = np.mean(in_areas[0:3])
        mean_areas[3] = np.mean(in_areas[1:4])
        mean_areas[4] = np.nan
        mean_areas[5] = np.nan
        mean_areas[6] = np.nan
        mean_areas[7] = np.nan
        mean_areas[8] = np.mean(in_areas[6:9])
        mean_areas[9] = np.mean(in_areas[7:10])

        in_extents = self.df.total_extent_km2
        mean_extents = np.zeros_like(in_extents)
        mean_extents[0] = np.mean(in_extents[0:1])
        mean_extents[1] = np.mean(in_extents[0:2])
        mean_extents[2] = np.nan
        mean_extents[3] = np.nan
        mean_extents[4] = np.mean(in_extents[2:5])
        mean_extents[5] = np.mean(in_extents[3:6])
        mean_extents[6] = np.mean(in_extents[4:7])
        mean_extents[7] = np.mean(in_extents[5:8])
        mean_extents[8] = np.mean(in_extents[6:9])
        mean_extents[9] = np.mean(in_extents[7:10])

        nday_average = 3
        min_valid = 1
        preserve_nan = True
        wrapped = False

        actual = warp.nday_average(self.df, nday_average, min_valid, preserve_nan, wrapped)
        expected = pd.DataFrame({'total_extent_km2': mean_extents,
                                 'total_area_km2': mean_areas},
                                index=self.daily_period_index)
        assert_frame_equal(expected, actual)

    def test_3day_window_1_min_valid(self):
        """Expect that extents are nday averaged properly with 3day window and 1 valid needed."""
        in_areas = self.df.total_area_km2
        mean_areas = np.zeros_like(in_areas)
        mean_areas[0] = np.mean(in_areas[0:1])
        mean_areas[1] = np.mean(in_areas[0:2])
        mean_areas[2] = np.mean(in_areas[0:3])
        mean_areas[3] = np.mean(in_areas[1:4])
        mean_areas[4] = np.mean(in_areas[2:5])
        mean_areas[5] = np.mean(in_areas[3:6])
        mean_areas[6] = np.nan
        mean_areas[7] = np.nan
        mean_areas[8] = np.mean(in_areas[6:9])
        mean_areas[9] = np.mean(in_areas[7:10])

        in_extents = self.df.total_extent_km2
        mean_extents = np.zeros_like(in_extents)
        mean_extents[0] = np.mean(in_extents[0:1])
        mean_extents[1] = np.mean(in_extents[0:2])
        mean_extents[2] = np.mean(in_extents[0:3])
        mean_extents[3] = np.mean(in_extents[1:4])
        mean_extents[4] = np.mean(in_extents[2:5])
        mean_extents[5] = np.mean(in_extents[3:6])
        mean_extents[6] = np.mean(in_extents[4:7])
        mean_extents[7] = np.mean(in_extents[5:8])
        mean_extents[8] = np.mean(in_extents[6:9])
        mean_extents[9] = np.mean(in_extents[7:10])

        nday_average = 3
        min_valid = 1
        preserve_nan = False
        wrapped = False

        actual = warp.nday_average(self.df, nday_average, min_valid, preserve_nan, wrapped)
        expected = pd.DataFrame({'total_extent_km2': mean_extents,
                                 'total_area_km2': mean_areas},
                                index=self.daily_period_index)
        assert_frame_equal(expected, actual)

    def test_3day_window_1_min_valid_rolling(self):
        """Expect that extents are nday averaged properly with rolling and 3day window
        and 1 valid needed."""
        in_areas = self.df.total_area_km2
        mean_areas = np.zeros_like(in_areas)
        mean_areas[0] = np.mean(np.append(in_areas[8:10], in_areas[0:1]))
        mean_areas[1] = np.mean(np.append(in_areas[9:10], in_areas[0:2]))
        mean_areas[2] = np.mean(in_areas[0:3])
        mean_areas[3] = np.mean(in_areas[1:4])
        mean_areas[4] = np.mean(in_areas[2:5])
        mean_areas[5] = np.mean(in_areas[3:6])
        mean_areas[6] = np.nan
        mean_areas[7] = np.nan
        mean_areas[8] = np.mean(in_areas[6:9])
        mean_areas[9] = np.mean(in_areas[7:10])

        in_extents = self.df.total_extent_km2
        mean_extents = np.zeros_like(in_extents)
        mean_extents[0] = np.mean(np.append(in_extents[8:10], in_extents[0:1]))
        mean_extents[1] = np.mean(np.append(in_extents[9:10], in_extents[0:2]))
        mean_extents[2] = np.mean(in_extents[0:3])
        mean_extents[3] = np.mean(in_extents[1:4])
        mean_extents[4] = np.mean(in_extents[2:5])
        mean_extents[5] = np.mean(in_extents[3:6])
        mean_extents[6] = np.mean(in_extents[4:7])
        mean_extents[7] = np.mean(in_extents[5:8])
        mean_extents[8] = np.mean(in_extents[6:9])
        mean_extents[9] = np.mean(in_extents[7:10])

        nday_average = 3
        min_valid = 1
        preserve_nan = False
        wrapped = True

        actual = warp.nday_average(self.df, nday_average, min_valid, preserve_nan, wrapped)
        expected = pd.DataFrame({'total_extent_km2': mean_extents,
                                 'total_area_km2': mean_areas},
                                index=self.daily_period_index)
        assert_frame_equal(expected, actual)

    def test_3day_window_2_min_valid(self):
        """Expect that extents are nday averaged properly with 3day window and 2 valid needed."""
        in_areas = self.df.total_area_km2
        mean_areas = np.zeros_like(in_areas)
        mean_areas[0] = np.nan  # first value is nan when min_valid is 2
        mean_areas[1] = np.mean(in_areas[0:2])
        mean_areas[2] = np.mean(in_areas[0:3])
        mean_areas[3] = np.mean(in_areas[1:4])
        mean_areas[4] = np.mean(in_areas[2:5])
        mean_areas[5] = np.nan
        mean_areas[6] = np.nan
        mean_areas[7] = np.nan
        mean_areas[8] = np.nan
        mean_areas[9] = np.mean(in_areas[8:10])

        in_extents = self.df.total_extent_km2
        mean_extents = np.zeros_like(in_extents)
        mean_extents[0] = np.nan    # first value is nan when min_valid is 2
        mean_extents[1] = np.mean(in_extents[0:2])
        mean_extents[2] = np.mean(in_extents[0:3])
        mean_extents[3] = np.nan
        mean_extents[4] = np.nan
        mean_extents[5] = np.mean(in_extents[3:6])
        mean_extents[6] = np.mean(in_extents[4:7])
        mean_extents[7] = np.mean(in_extents[5:8])
        mean_extents[8] = np.mean(in_extents[6:9])
        mean_extents[9] = np.mean(in_extents[7:10])

        nday_average = 3
        min_valid = 2
        preserve_nan = False
        wrapped = False

        actual = warp.nday_average(self.df, nday_average, min_valid, preserve_nan, wrapped)
        expected = pd.DataFrame({'total_extent_km2': mean_extents,
                                 'total_area_km2': mean_areas},
                                index=self.daily_period_index)
        assert_frame_equal(expected, actual)


class TestMeanAndStandardDeviation(unittest.TestCase):

    def setUp(self):
        """Set up dataframes."""
        datetimes = pd.DatetimeIndex([
            '1979-05-02', '1979-06-11',
            '1990-05-02', '1990-06-11',
            '2000-05-01', '2000-06-10',
            '2014-05-02', '2014-06-11',
        ])
        extents = [1000., 2000.,
                   500., 500.,
                   1000., 1000.,
                   2000., 3000.]

        self.df = pd.DataFrame({
            'total_extent_km2': extents,
        }, index=pd.to_datetime(datetimes))

    def test_climatology_years(self):
        expected_mean_doy_122 = np.mean([500., 1000.])
        expected_mean_doy_162 = np.mean([500., 1000.])

        expected_std_doy_122 = np.std([500., 1000.], ddof=1)
        expected_std_doy_162 = np.std([500., 1000.], ddof=1)

        actual = warp.mean_and_standard_deviation(self.df['total_extent_km2'], [1980, 2010])

        self.assertEqual(expected_mean_doy_122, actual.loc[122]['total_extent_km2_mean'])
        self.assertEqual(expected_std_doy_122, actual.loc[122]['total_extent_km2_std'])
        self.assertEqual(expected_mean_doy_162, actual.loc[162]['total_extent_km2_mean'])
        self.assertEqual(expected_std_doy_162, actual.loc[162]['total_extent_km2_std'])

    def test_basic_all_years(self):
        expected_mean_doy_122 = np.mean([1000., 500., 1000., 2000.])
        expected_mean_doy_162 = np.mean([2000., 500., 1000., 3000.])

        expected_std_doy_122 = np.std([1000., 500., 1000., 2000.], ddof=1)
        expected_std_doy_162 = np.std([2000., 500., 1000., 3000.], ddof=1)

        actual = warp.mean_and_standard_deviation(self.df['total_extent_km2'], [1979, 2015])

        self.assertEqual(expected_mean_doy_122, actual.loc[122]['total_extent_km2_mean'])
        self.assertEqual(expected_std_doy_122, actual.loc[122]['total_extent_km2_std'])
        self.assertEqual(expected_mean_doy_162, actual.loc[162]['total_extent_km2_mean'])
        self.assertEqual(expected_std_doy_162, actual.loc[162]['total_extent_km2_std'])


class TestQuantiles(unittest.TestCase):

        def setUp(self):
            """Set up dataframes."""
            datetimes = pd.DatetimeIndex([
                '1979-02-28', '1979-08-15',
                '1990-02-28', '1990-08-15',
                '1991-02-28', '1991-08-15',
                '1995-02-28', '1995-08-15',
                '1996-02-28', '1996-08-14',
                '2000-02-28', '2000-08-14',
                '2001-02-28', '2001-08-15',
                '2002-02-28', '2002-08-15',
                '2014-02-28', '2014-08-15',
                '2015-02-28', '2015-08-15'])
            extents = [100., 200.,
                       500., 500.,
                       400., 300.,
                       300., 400.,
                       900., 700.,
                       200., 100.,
                       600., 600.,
                       700., 800.,
                       800., 900.,
                       1000., 1000.]

            self.df = pd.DataFrame({
                'total_extent_km2': extents,
            }, index=datetimes)

        def test_all_years(self):
            """Quantile works with all years."""
            extents_doy_59 = np.array([100., 500., 400., 300., 900., 200., 600., 700., 800., 1000.])
            extents_doy_227 = np.array([200., 500., 300., 400., 700., 100., 600., 800., 900., 1000])

            q = np.array([.25, .75])

            quantiles_doy_59 = np.percentile(extents_doy_59, q*100, interpolation='linear')
            quantiles_doy_227 = np.percentile(extents_doy_227, q*100, interpolation='linear')
            expected_values_25, expected_values_75 = zip(quantiles_doy_59, quantiles_doy_227)

            expected_columns = pd.Float64Index([.25, .75])

            expected_index = pd.Int64Index([59, 227], name='day of year')

            actual = warp.quantiles(self.df['total_extent_km2'], [1979, 2015], q)

            assert_index_equal(actual.index, expected_index)
            assert_index_equal(actual.columns, expected_columns)
            npt.assert_array_equal(actual[0.25].values, expected_values_25)
            npt.assert_array_equal(actual[0.75].values, expected_values_75)

        def test_climatology_years(self):
            """Quantile works filtering some years."""
            extents_doy_59 = np.array([500., 400., 300., 900., 200., 600., 700.])
            extents_doy_227 = np.array([500., 300., 400., 700., 100., 600., 800.])

            q = np.array([.25, .75])

            quantiles_doy_59 = np.percentile(extents_doy_59, q*100, interpolation='linear')
            quantiles_doy_227 = np.percentile(extents_doy_227, q*100, interpolation='linear')
            expected_values_25, expected_values_75 = zip(quantiles_doy_59, quantiles_doy_227)

            expected_columns = pd.Float64Index([.25, .75])
            expected_index = pd.Int64Index([59, 227], name='day of year')

            actual = warp.quantiles(self.df, [1980, 2010], q)

            assert_index_equal(actual.index, expected_index)
            assert_index_equal(actual.columns, expected_columns)
            npt.assert_array_equal(actual[0.25].values, expected_values_25)
            npt.assert_array_equal(actual[0.75].values, expected_values_75)

        def test_with_missing_data(self):
            datetimes = pd.DatetimeIndex([
                '1979-02-28', '1979-08-15',
                '1981-02-28', '1981-08-15',
                '1990-02-28', '1990-08-15',
                '1991-02-28', '1991-08-15',
                '1995-02-28', '1995-08-15',
                '1996-02-28', '1996-08-14',
                '2000-02-28', '2000-08-14',
                '2001-02-28', '2001-08-15',
                '2002-02-28', '2002-08-15',
                '2013-02-28', '2013-08-15',
                '2014-02-28', '2014-08-15',
                '2015-02-28', '2015-08-15'])
            extents = [100., 200.,
                       0., 0.,
                       500., 500.,
                       np.nan, 300.,
                       300., 400.,
                       900., 700.,
                       200., 100.,
                       600., 600.,
                       700., np.nan,
                       400., 800,
                       800., 900.,
                       1000., 1000.]

            df = pd.DataFrame({
                'total_extent_km2': extents,
            }, index=datetimes)

            q = np.array([.3, .8])

            expected_values_30 = [300., 300.]
            expected_values_80 = [800., 800.]

            expected_columns = pd.Float64Index([.30, .80])

            expected_index = pd.Int64Index([59, 227], name='day of year')

            actual = warp.quantiles(df['total_extent_km2'], [1979, 2015], q)

            assert_index_equal(actual.index, expected_index)
            assert_index_equal(actual.columns, expected_columns)
            npt.assert_array_equal(actual[0.30].values, expected_values_30)
            npt.assert_array_equal(actual[0.80].values, expected_values_80)


class TestDropMissing(unittest.TestCase):

    def test_drop_without_missing_column_remains_same(self):
        df = pd.DataFrame(np.random.randn(4, 3), columns=['one', 'two', 'three'])
        expected = df.copy()
        actual = warp.drop_missing_columns(df)
        assert_frame_equal(expected, actual)

    def test_drop_with_missing_column(self):
        df = pd.DataFrame(np.random.randn(4, 3), columns=['one', 'two_missing', 'three'])
        actual = warp.drop_missing_columns(df)
        assert 'two_missing' not in actual.columns
        expected = df[['one', 'three']]
        assert_frame_equal(expected, actual)


class Test_ReorderDailySeriesByYears(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range(start='1979-01-01', end='2016-01-01')
        values = (np.random.randn(np.squeeze(dates.shape)) * 1000).astype(np.int)
        self.series = pd.Series(values, index=dates)

    def test_with_start_end_no_year(self):
        start = dt.date(2000, 2, 25)
        end = dt.date(2000, 3, 2)
        actual = warp._reorder_daily_series_by_years(self.series, start, end)
        expected = self.series[(self.series.index.date >= start) & (self.series.index.date <= end)]
        npt.assert_array_equal(expected.values, actual['2000'].values)

    def test_with_start_end_choose_years(self):
        start = dt.date(2000, 2, 25)
        end = dt.date(2000, 3, 2)

        # Leap year will align exactly
        expected80_start = dt.date(1980, 2, 25)
        expected80_end = dt.date(1980, 3, 2)
        expected80 = self.series[(self.series.index.date >= expected80_start) &
                                 (self.series.index.date <= expected80_end)]

        # Non Leap year will get an extra day
        expected85_start = dt.date(1985, 2, 25)
        expected85_end = dt.date(1985, 3, 3)
        expected85 = self.series[(self.series.index.date >= expected85_start) &
                                 (self.series.index.date <= expected85_end)]

        actual = warp._reorder_daily_series_by_years(self.series, start, end, years=[1980, 1985])

        npt.assert_array_equal(expected80.values, actual['1980'].values)
        npt.assert_array_equal(expected85.values, actual['1985'].values)
        self.assertSetEqual(set(actual.columns), set(['1980', '1985']))
        self.assertTrue('2000' not in actual.columns)

    def test_with_start_periods_choose_years(self):
        start = dt.date(2000, 2, 25)
        periods = 15

        # Leap year will align exactly
        expected84_start = dt.date(1984, 2, 25)
        expected84_end = expected84_start + dt.timedelta(periods - 1)
        expected84 = self.series[(self.series.index.date >= expected84_start) &
                                 (self.series.index.date <= expected84_end)]

        # Non Leap year will get an extra day
        expected85_start = dt.date(1985, 2, 25)
        expected85_end = expected85_start + dt.timedelta(periods - 1)
        expected85 = self.series[(self.series.index.date >= expected85_start) &
                                 (self.series.index.date <= expected85_end)]

        actual = warp._reorder_daily_series_by_years(self.series, start, periods=periods,
                                                     years=[1984, 1985])

        npt.assert_array_equal(expected84.values, actual['1984'].values)
        npt.assert_array_equal(expected85.values, actual['1985'].values)
        self.assertSetEqual(set(actual.columns), set(['1984', '1985']))


class Test_StackedClim(unittest.TestCase):

    def setUp(self):
        dates = pd.date_range(start='1979-01-01', end='2016-03-14')
        values = (np.random.randn(np.squeeze(dates.shape)) * 1000).astype(np.int)
        self.series = pd.Series(values, index=dates)

    def test_called_correctly(self):
        clim_years = (1990, 1993)
        expected_years = [1990, 1991, 1992, 1993]
        expected_start = dt.date(1990, 1, 1)
        expected_periods = 366

        with patch('seaice.timeseries.warp._reorder_daily_series_by_years') as patched:
            warp._stacked_clim(self.series, clim_years)
            patched.assert_called_with(self.series,
                                       expected_start,
                                       periods=expected_periods,
                                       years=expected_years)


class TestFilterColumns(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame(np.random.randn(4, 5),
                               columns=['one', 'two_missing', 'three', 'four', 'five'])

    def test_unchanged(self):
        expected = self.df.copy()
        actual = warp.filter_columns(self.df)
        assert_frame_equal(expected, actual)

    def test_filtered(self):
        expected = self.df.copy()
        expected = expected.drop(['one', 'two_missing'], axis=1)
        actual = warp.filter_columns(self.df, ['three', 'four', 'five'])
        assert_frame_equal(expected, actual)
