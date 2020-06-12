import datetime as dt
import unittest

import numpy as np
import numpy.testing as npt

import seaice.nasateam as nt
from seaice.nasateam.errors import SeaIceBadSeason
from .util import mock_today


class Test_datetime_index_for_seasonal_trends(unittest.TestCase):
    def test_starts_on_the_first_of_the_first_given_month(self):
        year = 2017
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index[0].day
        expected = 1
        self.assertEqual(actual, expected)

    def test_ends_on_the_last_of_the_last_given_month(self):
        year = 2017
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index[-1].day
        expected = 31
        self.assertEqual(actual, expected)

    def test_starts_within_the_satellite_era(self):
        year = 2015
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index[0].date()

        self.assertGreaterEqual(actual, nt.BEGINNING_OF_SATELLITE_ERA)

    def test_starts_in_satellite_year_2_when_given_season_that_is_incomplete_in_year_1(self):
        year = 2017
        months = (9, 10, 11)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = (actual_index[0].year, actual_index[0].month, actual_index[0].day)
        expected = (1979, 9, 1)
        self.assertEqual(actual, expected)

    def test_starts_near_the_beginning_of_satellite_era(self):
        year = 2015
        months = (9, 10, 11)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index[0].date()

        latest_start = nt.BEGINNING_OF_SATELLITE_ERA + dt.timedelta(365)

        self.assertGreaterEqual(latest_start, actual)

    def test_only_has_days_for_given_months(self):
        year = 2015
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = np.unique(actual_index.month)

        expected = np.array(months)

        npt.assert_array_equal(actual, expected)

    def test_only_goes_up_to_given_year(self):
        year = 2012
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index.year.max()

        expected = year

        self.assertEqual(actual, expected)

    @mock_today(2013, 10, 28)
    def test_only_goes_up_to_previous_year_if_given_season_is_incomplete(self):
        year = 2013
        months = (9, 10, 11)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index.year.max()

        expected = 2012

        self.assertEqual(actual, expected)

    @mock_today(2013, 10, 28)
    def test_only_goes_up_to_current_year_when_given_future_yearseason(self):
        year = 2014
        months = (3, 4, 5)

        actual_index = nt.datetime_index_for_seasonal_trends(year, months)
        actual = actual_index.year.max()

        expected = 2013

        self.assertEqual(actual, expected)


class Test_validate_seasons(unittest.TestCase):
    def test_default_seasons_are_valid(self):
        seasons = {
            'spring': (3, 4, 5),
            'summer': (6, 7, 8),
            'autumn': (9, 10, 11),
            'winter': (12, 1, 2)
        }
        nt.validate_seasons(seasons)

    def test_custom_seasons_are_valid(self):
        seasons = {
            'spring': (1, 2, 3),
            'summer': (4, 5, 6),
            'autumn': (7, 8, 9),
            'winter': (10, 11, 12)
        }
        nt.validate_seasons(seasons)

    def test_raises_error_if_month_is_skipped(self):
        seasons = {
            'spring': (3, 5, 6)
        }
        with self.assertRaises(SeaIceBadSeason):
                    nt.validate_seasons(seasons)

    def test_raises_error_if_out_of_order(self):
        seasons = {
            'spring': (4, 3, 5)
        }
        with self.assertRaises(SeaIceBadSeason):
                    nt.validate_seasons(seasons)

    def test_raises_error_if_december_not_immediately_followed_by_january(self):
        seasons = {
            'winter': (12, 13, 1)
        }
        with self.assertRaises(SeaIceBadSeason):
                    nt.validate_seasons(seasons)

    def test_raises_error_if_less_than_three_months(self):
        seasons = {
            'spring': (3, 4)
        }
        with self.assertRaises(SeaIceBadSeason):
                    nt.validate_seasons(seasons)

    def test_raises_error_if_more_than_three_months(self):
        seasons = {
            'spring': (3, 4, 5, 6)
        }
        with self.assertRaises(SeaIceBadSeason):
                    nt.validate_seasons(seasons)
