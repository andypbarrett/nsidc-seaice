import unittest

import pandas as pd
import numpy.testing as npt

from .. import warp


class TestSplitByColumn(unittest.TestCase):
    def test_creates_a_new_dataframe_for_each_passed_value(self):
        df = pd.DataFrame.from_dict({'hemi': ['N', 'S', 'S', 'E']}, orient='columns')

        dfs = warp.split_by_column(df, 'hemi', ['N'])
        self.assertEqual(len(dfs), 1)
        self.assertEqual(set(dfs[0].hemi.values), {'N'})

        dfs = warp.split_by_column(df, 'hemi', ['N', 'S'])
        self.assertEqual(len(dfs), 2)
        self.assertEqual(set(dfs[0].hemi.values), {'N'})
        self.assertEqual(set(dfs[1].hemi.values), {'S'})


class TestOrderByRank(unittest.TestCase):
    def test_sorts_by_rank(self):
        df = pd.DataFrame(
            data={
                'extent': [100, 20, 30, 40],
                'year': [2000, 1920, 1930, 1940],
            },
            index=pd.DatetimeIndex(['2001', '2002', '2003', '2004'])
        )

        expected_ranked_extent = pd.Series([20, 30, 40, 100])
        expected_ranked_years = pd.Series([1920, 1930, 1940, 2000])

        actual = warp.order_by_rank(df)

        npt.assert_array_equal(expected_ranked_years, actual['ranked-year'].values)
        npt.assert_array_equal(expected_ranked_extent, actual['ranked-extent'].values)


class Test_restrict_filename(unittest.TestCase):

    def setUp(self):
        filenames1 = ['nt_20150731_f17_v1.1_s.bin',
                      'nt_20150801_f17_v1.1_s.bin',
                      'nt_20150802_f17_v1.1_s.bin']
        filenames7 = ['nt_20150807_f17_v1.1_s.bin']
        filenames8 = []

        df = pd.DataFrame([[pd.Timestamp('2015-08-01'), filenames1],
                           [pd.Timestamp('2015-08-07'), filenames7],
                           [pd.Timestamp('2015-08-08'), filenames8]],
                          columns=['date', 'filename'])
        df = df.set_index('date')

        self.df = df

    def test_picks_filename_matching_the_date(self):
        actual = warp.restrict_filename(self.df)

        actual_filename = actual.loc['2015-08-01', 'filename']

        expected = 'nt_20150801_f17_v1.1_s.bin'

        self.assertEqual(actual_filename, expected)

    def test_uses_the_only_available_filename(self):
        actual = warp.restrict_filename(self.df)

        actual_filename = actual.loc['2015-08-07', 'filename']

        expected = 'nt_20150807_f17_v1.1_s.bin'

        self.assertEqual(actual_filename, expected)

    def test_with_empty_filename_list(self):
        actual = warp.restrict_filename(self.df)

        actual_filename = actual.loc['2015-08-08', 'filename']

        expected = ''

        self.assertEqual(actual_filename, expected)
