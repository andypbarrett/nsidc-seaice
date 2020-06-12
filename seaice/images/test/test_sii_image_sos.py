import datetime as dt
import unittest

import pandas as pd
import pandas.util.testing as pdt

import seaice.images.cli.sii_image_sos as sii_image_sos


class Test__datetime_indexes(unittest.TestCase):
    def test_divides_range_evenly_based_on_given_size(self):
        start_date = dt.date(2000, 1, 1)
        end_date = dt.date(2000, 1, 6)
        days_per_image = 3
        all_dates = False

        actual = sii_image_sos._datetime_indexes(start_date,
                                                 end_date,
                                                 days_per_image,
                                                 all_dates,
                                                 month=None)

        expected = [pd.date_range(start='2000-01-01', end='2000-01-03', freq='D'),
                    pd.date_range(start='2000-01-04', end='2000-01-06', freq='D')]

        pdt.assert_index_equal(expected[0], actual[0])
        pdt.assert_index_equal(expected[1], actual[1])

    def test_adds_days_if_range_cannot_be_divided_evenly(self):
        start_date = dt.date(2000, 1, 1)
        end_date = dt.date(2000, 1, 4)
        days_per_image = 3
        all_dates = False

        actual = sii_image_sos._datetime_indexes(start_date,
                                                 end_date,
                                                 days_per_image,
                                                 all_dates,
                                                 month=None)

        expected = [pd.date_range(start='2000-01-01', end='2000-01-03', freq='D'),
                    pd.date_range(start='2000-01-04', end='2000-01-06', freq='D')]

        pdt.assert_index_equal(expected[0], actual[0])
        pdt.assert_index_equal(expected[1], actual[1])

    def test_to_start_of_satellite_era_if_all_is_true(self):
        start_date = dt.date(2000, 1, 1)
        end_date = dt.date(2000, 1, 4)
        days_per_image = 3
        all_dates = True

        actual = sii_image_sos._datetime_indexes(start_date,
                                                 end_date,
                                                 days_per_image,
                                                 all_dates,
                                                 month=None)

        expected = pd.date_range(start='1978-10-26', end='1978-10-28', freq='D')

        pdt.assert_index_equal(expected, actual[0])

    def test_with_all_and_a_given_month(self):
        start_date = None
        end_date = None
        days_per_image = 10
        all_dates = True

        actual = sii_image_sos._datetime_indexes(start_date,
                                                 end_date,
                                                 days_per_image,
                                                 all_dates,
                                                 month=9)

        expected = []
        expected.append(pd.date_range(start='1979-09-01', end='1979-09-10', freq='D'))
        expected.append(pd.date_range(start='1979-09-11', end='1979-09-20', freq='D'))
        expected.append(pd.date_range(start='1979-09-21', end='1979-09-30', freq='D'))
        expected.append(pd.date_range(start='1980-09-01', end='1980-09-10', freq='D'))

        for i in range(4):
            pdt.assert_index_equal(expected[i], actual[i])
