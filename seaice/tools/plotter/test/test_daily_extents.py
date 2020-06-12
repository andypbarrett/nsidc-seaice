import datetime as dt
import unittest

import pandas as pd
import numpy as np
import numpy.testing as npt

import seaice.nasateam as nt
import seaice.tools.plotter.daily_extent as de


class Test_BoundingDateRange(unittest.TestCase):

    def test_standard(self):
        today = dt.date(2015, 9, 22)
        month_bounds = (-3, 1)
        expected_bounds = (dt.date(2015, 6, 1), dt.date(2015, 10, 31))
        actual = de._bounding_date_range(today, *month_bounds)

        self.assertEqual(expected_bounds, actual)

    def test_bounding_dates_overlap_year(self):
        today = dt.date(2001, 1, 15)
        month_bounds = (-1, 1)

        expected_bounds = (dt.date(2000, 12, 1), dt.date(2001, 2, 28))
        actual = de._bounding_date_range(today, *month_bounds)

        self.assertEqual(expected_bounds, actual)

    def test_bounding_dates_overlap_leap_year(self):
        today = dt.date(2016, 1, 15)
        month_bounds = (-1, 1)

        expected_bounds = (dt.date(2015, 12, 1), dt.date(2016, 2, 29))
        actual = de._bounding_date_range(today, *month_bounds)

        self.assertEqual(expected_bounds, actual)


class Test_GetRecordYear(unittest.TestCase):
    start_date = nt.BEGINNING_OF_SATELLITE_ERA
    end_date = dt.date(2015, 12, 31)
    date_index = pd.date_range(start_date, end_date)
    base_series = pd.Series(index=date_index).fillna(5)

    def _series(self, low=None, high=None, next_highest=None, next_lowest=None):
        """Return a series for easily testing record values. All the values are 5, with
        different values set to the dates passed in as low, next_lowest, high,
        and next_highest. The index of the returned series is from the beginning
        of the satellite era to the end of 2015 (since that happens to be the
        last complete year at the time of this writing).

        """
        series = self.base_series.copy()

        if high:
            series[high] = 10

        if next_highest:
            series[next_highest] = 7

        if next_lowest:
            series[next_lowest] = 2

        if low:
            series[low] = 0

        return series

    def test_max(self):
        """Date: 4/2014, range: 1/2014 -> 5/2014, record:9/2002 , recordline:2002"""
        series = self._series(high='2002-09-15')

        date = pd.to_datetime('2014-04-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2002

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min(self):
        """Date: 4/2014, range: 1/2014 -> 5/2014, record:9/2002(min) , recordline:2002"""
        series = self._series(low='2002-09-15')

        date = pd.to_datetime('2014-04-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2002

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_current_year_is_record(self):
        """Date: 4/2014, range: 1/2014 -> 5/2014, record:3/2014, recordline:2010"""
        series = self._series(high='2014-03-15', next_highest='2010-09-15')

        date = pd.to_datetime('2014-04-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2010

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_current_year_is_record(self):
        """Date: 4/2014, range: 1/2014 -> 5/2014, record:3/2014(min), recordline:2010"""
        series = self._series(low='2014-03-15', next_lowest='2010-09-15')

        date = pd.to_datetime('2014-04-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2010

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_min_record_year_is_included_in_month_bounds(self):
        """Date: 2/2015, range: 10/2014 -> 3/2015, record: 1/2014, recordline: 2013-2014"""
        series = self._series(low='2014-04-20', next_lowest='1999-09-15')

        date = pd.to_datetime('2015-02-15')

        month_bounds = (-4, 1)

        # expectation
        expected = 2014

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_min_record_year_before_and_crossover_forward(self):
        """Date: 12/2015, range: 8/2015 -> 1/2016, record: 12/2014, recordline: 2014-2015"""
        series = self._series(low='2014-09-20', next_lowest='1999-09-15')

        date = pd.to_datetime('2015-12-15')

        month_bounds = (-4, 1)

        # expectation
        expected = 2014

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_changeover_record_is_plotted_and_aligned(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:1/2004, recordline:2004"""
        series = self._series(high='2004-01-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2004

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_changeover_record_is_plotted_and_aligned(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:1/2004(min), recordline:2003-2004"""
        series = self._series(low='2004-01-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2004

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_changeover_record_is_plotted_not_aligned(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:11/2007 , recordline:2007-2008"""
        series = self._series(high='2007-11-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2008

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_changeover_record_is_plotted_not_aligned(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:11/2007 , recordline:2007-2008"""
        series = self._series(low='2007-11-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2008

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_changeover_record_is_plotted_with_current_year_plots_next_highest(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:11/2009 , recordline:2004-2005"""
        series = self._series(high='2009-11-27', next_highest='2004-11-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2005

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_changeover_record_is_plotted_with_current_year_plots_next_highest(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record:11/2009 , recordline:2004-2005"""
        series = self._series(low='2009-11-27', next_lowest='2004-11-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2005

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_record_not_plotted_picks_most_months(self):
        """Date: 1/2010, range: 11/2009 -> 3/2010, record:10/2008, recordline:2007-2008"""
        series = self._series(high='2008-10-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-2, 2)

        # expectation
        expected = 2008

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_record_not_plotted_picks_most_months(self):
        """Date: 1/2010, range: 11/2009 -> 3/2010, record:8/2008, recordline:2007-2008"""

        series = self._series(low='2008-08-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-2, 2)

        # expectation
        expected = 2008

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_record_not_plotted_picks_most_months_next_highest_record(self):
        """Date: 1/2010, range: 10/2009 -> 2/2010, record: 8/2009, recordline: 2008-2009 """
        series = self._series(high='2009-08-27', next_highest='2004-08-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2009

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_record_not_plotted_picks_most_months_next_highest_record(self):
        """Date: 1/2010, range:10/2009 -> 2/2010, record: 8/2009, recordline: 2008-2009"""
        series = self._series(low='2009-08-27', next_lowest='2004-08-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2009

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_past_record_same_year(self):
        """Date: 9/2015, range:6/2015 -> 10/2015, record: 3/2015, recordline: 2010"""
        series = self._series(low='2015-03-27', next_lowest='2010-03-28')

        date = pd.to_datetime('2015-09-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2010

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_past_record_same_year_with_overlap(self):
        """Date: 9/2015, range:6/2015 -> 1/2016, record: 3/2015, recordline: 2014-2015"""
        series = self._series(low='2015-03-27', next_lowest='2010-03-28')

        date = pd.to_datetime('2015-09-15')

        month_bounds = (-3, 4)

        # expectation
        expected = 2014

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)

    def test_max_year_record_not_plotted_same_most_months_picks_earlier_year(self):
        """Date: 1/2010, range: 11/2009 -> 2/2010, record: 8/2008 , recordline:2008-2009"""
        series = self._series(high='2008-08-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-2, 1)

        # expectation
        expected = 2009

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_starts_january_contains_record_month_same_year(self):
        """Date: 12/09, range: 09/2009 -> 1/2010, record: 9/2008 , recordline:2008-2009"""
        series = self._series(high='2008-09-22')

        date = pd.to_datetime('2009-12-15')

        month_bounds = (-3, 1)

        # expectation
        expected = 2008

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_starts_feb_contains_record_month_different_year(self):
        """Date: 1/10, range: 09/2009 -> 2/2010, record: 9/2008 , recordline:2008-2009"""
        series = self._series(high='2008-09-22')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-4, 1)

        # expectation
        expected = 2009

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'max')

        self.assertEqual(actual, expected)

    def test_min_year_record_not_plotted_same_most_months_picks_earlier_year(self):
        """Date: 1/2010, range: 11/2009 -> 2/2010, record:8/2008 , recordline:2008-2009"""
        series = self._series(low='2008-08-27')

        date = pd.to_datetime('2010-01-15')

        month_bounds = (-2, 1)

        # expectation
        expected = 2009

        # execute
        actual = de._get_record_year(series, date, month_bounds, 'min')

        self.assertEqual(actual, expected)


class Test_YearWithMostMonthsInIndex(unittest.TestCase):

    def test_longer_year_earlier(self):
        index = pd.date_range(start='1999-01-01', end='2000-01-31')
        actual = de._year_with_most_months_in_index(index)
        expected = 1999
        self.assertEqual(actual, expected)

    def test_longer_year_later(self):
        index = pd.date_range(start='1999-11-01', end='2000-04-29')
        actual = de._year_with_most_months_in_index(index)
        expected = 2000
        self.assertEqual(actual, expected)

    def test_earlier_year_when_equal_months(self):
        index = pd.date_range(start='1999-11-01', end='2000-02-29')
        actual = de._year_with_most_months_in_index(index)
        expected = 1999
        self.assertEqual(actual, expected)


class Test_DateIndexPrependDays(unittest.TestCase):
    def test_adds_days_to_beginning_of_date_index(self):
        date_index = pd.date_range(start='2005-01-05', end='2005-01-10')
        days = 5

        actual = de._date_index_prepend_days(date_index, days)
        expected = pd.date_range(start='2004-12-31', end='2005-01-10')

        self.assertTrue(actual.equals(expected))


class Test__ExtendSmoothDivide(unittest.TestCase):
    def test_does_all_the_things(self):
        date_index = pd.date_range(start='2000-01-06', end='2000-01-08')
        nday_average = 3
        divisor = 1e3

        df_index = pd.Index([6, 7, 8], name='day of year')
        df = pd.DataFrame({'data': [10000, 15000, 20000]}, index=df_index)

        actual = de._extend_smooth_divide(df, date_index, nday_average, divisor)

        # index extended
        expected_index = pd.Index([3, 4, 5, 6, 7, 8])
        npt.assert_array_equal(actual.index.values, expected_index.values)

        # smoothed and divided
        expected_data = np.array([np.nan, np.nan, np.nan, 10, 12.5, 15])
        npt.assert_array_equal(actual.data.values, expected_data)


class Test_ClimatologyStatistics(unittest.TestCase):

    def test_with_data_gets_average_stddevs_and_percentiles(self):
        date_index = pd.date_range(start='2008-01-01', end='2008-01-10')

        series1 = pd.Series([1000.0,
                             2000.0,
                             3000.0,
                             4000.0,
                             5000.0],
                            index=pd.date_range(start='2008-01-03', end='2008-01-07'))
        series2 = pd.Series([2000.0,
                             3000.0,
                             4000.0,
                             5000.0,
                             6000.0],
                            index=pd.date_range(start='2009-01-03', end='2009-01-07'))
        extents = series1.append(series2)
        extents.name = 'total_extent_km2'

        actual = de._climatology_statistics(extents, date_index,
                                            percentiles=[0, 50, 100], nday_average=3, divisor=1e3)

        expected_columns = ['climatology', 'climatology_lower', 'climatology_upper',
                            'percentile_0', 'percentile_50', 'percentile_100']
        npt.assert_array_equal(sorted(actual.columns), sorted(expected_columns))

        expected_climatology = [np.nan, np.nan, 1.5, 2., 2.5, 3.5, 4.5, 5., 5.5, np.nan]
        expected_climatology_upper = [np.nan, np.nan, 2.914214, 3.414214, 3.914214, 4.914214,
                                      5.914214, 6.414214, 6.914214, np.nan]
        expected_climatology_lower = [np.nan, np.nan, 0.085786, 0.585786, 1.085786, 2.085786,
                                      3.085786, 3.585786, 4.085786, np.nan]

        npt.assert_array_equal(actual.climatology, expected_climatology)
        npt.assert_array_almost_equal(actual.climatology_upper, expected_climatology_upper)
        npt.assert_array_almost_equal(actual.climatology_lower, expected_climatology_lower)

        expected_percentile_100 = [np.nan, np.nan, 2., 2.5, 3., 4., 5., 5.5, 6., np.nan]
        npt.assert_array_equal(actual.percentile_100, expected_percentile_100)

        expected_percentile_50 = [np.nan, np.nan, 1.5, 2., 2.5, 3.5, 4.5, 5., 5.5, np.nan]
        npt.assert_array_equal(actual.percentile_50, expected_percentile_50)

        expected_percentile_0 = [np.nan, np.nan, 1., 1.5, 2., 3., 4., 4.5, 5., np.nan]
        npt.assert_array_equal(actual.percentile_0, expected_percentile_0)
