import unittest

import numpy as np
import pandas as pd

import seaice.tools.plotter.monthly_anomaly as plt


class Test__mean_string(unittest.TestCase):

    def test_includes_the_climatology_years_and_mean_extent(self):
        x = pd.period_range(start='1979-01', end='1985-01', freq='M')
        x = x[x.month == 1]
        y = np.ma.array([7.46,  3.49,  15.12,  15.57,  15.3,   15.15, 15.34])

        series = pd.Series(y, index=x)

        actual = plt._mean_string(series, 1)

        expected = '1981-2010 mean = 15.3 million sq km'

        self.assertEqual(expected, actual)


class Test__slope_string(unittest.TestCase):

    def test_includes_the_slope_and_uncertainty(self):
        x = pd.period_range(start='1979-01', end='1999-01', freq='M')
        x = x[x.month == 1]
        y = np.ma.array([15.46,  15.49,  15.12,  15.57,  15.3,   15.15, 15.34,
                         12.46,  12.49,  12.12,  12.57,  12.3,   12.12, 12.34,
                         11.46,  11.49,  11.12,  11.57,  11.3,   11.11, 11.34])
        df = pd.DataFrame({'anomaly': y}, index=x)

        actual = plt._slope_string(df)

        expected = '-2.6 ± 0.5 %'

        self.assertEqual(expected, actual)


class Test__round_to_nearest_multiple_up(unittest.TestCase):
    def test_rounds_up_to_multiple_of_5(self):
        actual = plt._round_to_nearest_multiple_up(6)
        expected = 10
        self.assertEqual(expected, actual)

    def test_rounds_up_to_multiple_of_given_param(self):
        actual = plt._round_to_nearest_multiple_up(6, 4)
        expected = 8
        self.assertEqual(expected, actual)


class Test__round_to_nearest_multiple_down(unittest.TestCase):
    def test_rounds_down_to_multiple_of_5(self):
        actual = plt._round_to_nearest_multiple_down(6)
        expected = 5
        self.assertEqual(expected, actual)

    def test_rounds_down_to_multiple_of_given_param(self):
        actual = plt._round_to_nearest_multiple_down(6, 4)
        expected = 4
        self.assertEqual(expected, actual)


class Test__y_range(unittest.TestCase):
    def test_default_values(self):
        actual = plt._y_range([1, 2, 3, 4])
        expected = [-25, 25]
        self.assertEqual(expected, actual)

    def test_increase_upper_bound(self):
        actual = plt._y_range([1, 2, 3, 4, 26])
        expected = [-25, 30]
        self.assertEqual(expected, actual)

    def test_decrease_lower_bound(self):
        actual = plt._y_range([1, 2, 3, 4, -26])
        expected = [-30, 25]
        self.assertEqual(expected, actual)

    def test_increase_upper_bound_when_too_close(self):
        actual = plt._y_range([1, 2, 3, 4, 29])
        expected = [-25, 35]
        self.assertEqual(expected, actual)

    def test_decrease_lower_bound_when_too_close(self):
        actual = plt._y_range([1, 2, 3, 4, -29])
        expected = [-35, 25]
        self.assertEqual(expected, actual)


class Test__directory_subdir(unittest.TestCase):

    def test_makes_expected(self):
        expected = 'north/monthly/06_Jun'
        actual = plt._directory_subdir('N', 6)
        self.assertEqual(expected, actual)
