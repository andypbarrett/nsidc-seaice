import os
from unittest import TestCase

import pandas as pd

import seaice.datastore.fixture as fixture


class Test_from_daily_csv(TestCase):
    def test_from_daily_csv(self):
        frame = fixture.from_daily_csv(os.path.realpath('seaice/datastore/test/fixtures/daily.csv'))
        self.assertEqual(frame.index.names, ['date', 'hemisphere'])
        self.assertTrue((frame.index.levels[0] == pd.date_range(start='2015-08-01',
                                                                periods=8,
                                                                freq='D').to_period()).all)
        self.assertNotIn('date', frame.columns)
        self.assertNotIn('hemisphere', frame.columns)


class Test__read_csv(TestCase):
    def test_failed_read_throws_custom_error(self):
        self.assertRaises(fixture.SeaicedatastoreDataStoreNotFoundError,
                          fixture._read_csv, 'foobarfoobar')


class Test_from_monthly_csv(TestCase):
    def test_from_monthly_csv(self):
        monthly_fixture = os.path.realpath('seaice/datastore/test/fixtures/monthly.csv')
        frame = fixture.from_monthly_csv(monthly_fixture)
        self.assertEqual(frame.index.names, ['month', 'hemisphere'])
        self.assertTrue((frame.index.levels[0] == pd.date_range(start='2015-11',
                                                                periods=5,
                                                                freq='M').to_period()).all)
        self.assertNotIn('month', frame.columns)
        self.assertNotIn('hemisphere', frame.columns)
