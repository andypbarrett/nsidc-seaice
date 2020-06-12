from os.path import dirname, join
import unittest

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt

from .. import api


# in this datastore, every date's extent is equal to that date's month for dates
# in 1981-2010, otherwise it is that date's day-of-month, times 1e6
#
# Some examples:
#
# 1979-09-20: 20 * 1e6 sq km
# 1988-03-21: 3 * 1e6 sq km
# 2000-12-11: 12 * 1e6 sq km
# 2011-05-02: 2 * 1e6 sq km
DAILY_DATASTORE = join(dirname(__file__), 'fixtures', 'daily.p')


class TestMonthlyAnomaly(unittest.TestCase):

    def test_to_show_working_multiple_months(self):

        index = pd.PeriodIndex(['1979-01', '1979-02', '1980-01', '1980-02', '1981-01', '1981-02',
                                '1982-01', '1982-02', '1983-01', '1983-02', '1984-01', '1984-02',
                                '1985-01', '1985-02'], name='month', freq='M')

        areas = np.array([15., 25., 15., 25., 50., 50.,
                          50., 50., 15., 25., 15., 25.,
                          15., 25.])

        extents = np.array([150., 250., 150., 250., 500., 500.,
                            500., 500., 150., 250., 150., 250.,
                            150., 250.])

        df = pd.DataFrame({
            'total_extent_km2': extents,
            'total_area_km2': areas
        }, index=index)

        expected_areas = areas - 50.
        expected_extents = extents - 500.

        actual_extents = api.monthly_anomaly(df['total_extent_km2'], (1981, 1982))
        actual_areas = api.monthly_anomaly(df['total_area_km2'], (1981, 1982))

        npt.assert_array_equal(expected_extents, actual_extents)
        npt.assert_array_equal(expected_areas, actual_areas)


class TestMonthlyPercentAnomaly(unittest.TestCase):

    def test_monthly_percent_anomaly(self):

        clim_years = (1981, 1982)
        index = pd.PeriodIndex(['1979-01', '1979-02', '1980-01', '1980-02', '1981-01',
                                '1981-02', '1982-01', '1982-02', '1983-01', '1983-02',
                                '1984-01', '1984-02', '1985-01', '1985-02'],
                               name='month', freq='M')

        series = pd.Series(np.arange(14., dtype=np.float), index=index)

        jan = series[series.index.month == 1]
        clim_mean_jan = jan[(jan.index.year == 1981) | (jan.index.year == 1982)].mean()
        feb = series[series.index.month == 2]
        clim_mean_feb = feb[(feb.index.year == 1981) | (feb.index.year == 1982)].mean()
        jan_percent = 100 * (jan - clim_mean_jan) / clim_mean_jan
        feb_percent = 100 * (feb - clim_mean_feb) / clim_mean_feb

        expected = pd.concat([jan_percent, feb_percent], sort=True).sort_index()

        actual = api.monthly_percent_anomaly(series, clim_years)
        pdt.assert_series_equal(expected, actual)


class TestTrend(unittest.TestCase):

    def test_trend(self):
        index = pd.PeriodIndex(['1979-01', '1980-01', '1981-01',
                                '1982-01', '1983-01',
                                '1984-01', '1985-01'],
                               name='month', freq='M')

        arr = np.array([0, 1, 2, 3, 4, 5, 6], dtype=np.float)
        series = pd.Series(arr, index=index)

        actual = api.trend(series)

        expected = [0, 1, 2, 3, 4, 5, 6]

        npt.assert_array_almost_equal(expected, actual)

    def test_trend_with_missing(self):
        index = pd.PeriodIndex(['1979-01', '1980-01', '1981-01',
                                '1982-01', '1983-01',
                                '1984-01', '1985-01'],
                               name='month', freq='M')

        arr = np.array([0, 1, 2, np.nan, 4, 5, 6], dtype=np.float)
        series = pd.Series(arr, index=index)

        actual = api.trend(series)

        expected = pd.Series(np.array([0, 1, 2, 3, 4, 5, 6], dtype=np.float), index=index)

        pdt.assert_series_equal(expected, actual)


class Test_climatology_average_rates_of_change(unittest.TestCase):

    def test_averages_only_climatology_years(self):
        # for all months except January, the expected change is 1; if the
        # average incorporates data from outside of 1981-2010, the actual value
        # will be wrong
        expected_feb_change = 1

        actual_df = api.climatology_average_rates_of_change(
            hemisphere='N',
            data_store=DAILY_DATASTORE
        )

        actual = actual_df['ice change Mkm^2 per month'].iloc[2]

        self.assertEqual(expected_feb_change, actual)
