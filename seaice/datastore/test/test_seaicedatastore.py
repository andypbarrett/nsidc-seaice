import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

import seaice.datastore.seaicedatastore as sds
import seaice.datastore.fixture as fixture


class Test_write_datastore(TestCase):
    def setUp(self):
        self.frame = pd.DataFrame(np.random.randint(0, 100, size=(20, 6)), columns=list('ABCDEF'))
        self.frame['hemisphere'] = 'N'
        self.frame['date'] = pd.date_range(start='2015-01-01', periods=20, freq='D')
        self.frame.set_index(['date', 'hemisphere'], inplace=True)

    @patch('pandas.DataFrame.to_pickle')
    def test_write_datastore(self, to_pickle):
        data_store = '/tmp/tmp.p'
        to_pickle.return_value = True
        sds.write_datastore(self.frame.copy(), data_store, self.frame.columns)
        to_pickle.assert_called_with(data_store)

    @patch('pandas.DataFrame.to_pickle')
    def test_write_datastore_with_column_list(self, to_pickle):
        data_store = '/tmp/tmp.p'
        to_pickle.return_value = True
        frame = MagicMock(wraps=self.frame)
        frame.sort_index.return_value = frame
        sds.write_datastore(frame, data_store, ['foo', 'bar'])
        frame.__getitem__.assert_called_with(['foo', 'bar'])

    @patch('pandas.DataFrame.to_pickle')
    def test_write_datastore_with_default_column_list(self, to_pickle):
        data_store = '/tmp/tmp.p'
        to_pickle.return_value = True
        frame = MagicMock(wraps=self.frame)
        frame.sort_index.return_value = frame
        sds.write_datastore(frame, data_store)
        frame.__getitem__.assert_called_with(frame.columns)


class Test_new_dataframe(TestCase):
    def test_invalid_frequency(self):
        self.assertRaises(sds.SeaicedatastoreError, sds.new_dataframe, None)


class Test_read_datastore(TestCase):
    csv_path = (os.path.realpath('seaice/datastore/test/fixtures/daily.csv'))
    fixture_filename = 'daily.p'

    def removeTestOutput(self):
        try:
            os.remove(self.fixture_filename)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()
        frame = fixture.from_daily_csv(self.csv_path)
        frame.to_pickle(self.fixture_filename)

    def tearDown(self):
        self.removeTestOutput()

    def test_read_datastore(self):
        frame = sds.read_datastore(os.path.realpath(self.fixture_filename))

        self.assertTrue(frame.index.names == ['date', 'hemisphere'])
        self.assertTrue((frame.index.levels[0] == pd.date_range(start='2015-08-01',
                                                                periods=8,
                                                                freq='D').to_period()).all)
        self.assertFalse('date' in frame.columns)
        self.assertFalse('hemisphere' in frame.columns)


class Test_read_datastore_throws_error_on_not_found(TestCase):
    def test_failed_read_throws_custom_Error(self):
        self.assertRaises(sds.SeaicedatastoreDataStoreNotFoundError, sds.read_datastore, 'foobar')


class Test_read_monthly_datastore(TestCase):
    csv_path = (os.path.realpath('seaice/datastore/test/fixtures/monthly.csv'))
    fixture_filename = 'monthly.p'

    def removeTestOutput(self):
        try:
            os.remove(self.fixture_filename)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()
        frame = fixture.from_monthly_csv(self.csv_path)
        frame.to_pickle(self.fixture_filename)

    def tearDown(self):
        self.removeTestOutput()

    def test_read_monthly(self):
        frame = sds.read_datastore(self.fixture_filename)

        self.assertTrue(frame.index.names == ['month', 'hemisphere'])
        self.assertTrue((frame.index.levels[0] == pd.date_range(start='2015-11',
                                                                periods=5,
                                                                freq='M').to_period()).all)
        self.assertFalse('month' in frame.columns)
        self.assertFalse('hemisphere' in frame.columns)


class Test_index_label(TestCase):
    def test_date(self):
        self.assertEqual('date', sds.index_label('D'))

    def test_month(self):
        self.assertEqual('month', sds.index_label('M'))


class Test_get_bad_days_for_hemisphere(TestCase):
    csv_path = (os.path.realpath('seaice/datastore/test/fixtures/daily.csv'))
    fixture_filename = 'daily.p'

    def removeTestOutput(self):
        try:
            os.remove(self.fixture_filename)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()
        frame = fixture.from_daily_csv(self.csv_path)
        frame.to_pickle(self.fixture_filename)

    def tearDown(self):
        self.removeTestOutput()

    def _get_test_dataframe(self):
        df = pd.DataFrame(index=pd.PeriodIndex([], freq='D', name='date'),
                          columns=['hemisphere', 'foo', 'bar'])
        df = df.set_index([df.index, 'hemisphere'])
        df.at[(pd.Period('2015-01-01', 'D'), 'N'), 0] = 0
        return df

    def test_get_bad_days_for_hemisphere_with_bad_days(self):
        bad_days = sds.get_bad_days_for_hemisphere('S', self.fixture_filename)
        self.assertEqual(bad_days, [pd.Period('2015-08-04', 'D'), pd.Period('2015-08-06', 'D')])

    def test_get_bad_days_for_hemisphere_with_no_bad_days(self):
        bad_days = sds.get_bad_days_for_hemisphere('N', self.fixture_filename)
        self.assertEqual(bad_days, [])

    @patch('seaice.datastore.seaicedatastore.read_datastore')
    def test_get_bad_days_for_hemisphere_with_no_failed_qa_column(self, read_datastore):
        df = self._get_test_dataframe()
        read_datastore.return_value = df
        bad_days = sds.get_bad_days_for_hemisphere('S', self.fixture_filename)
        self.assertEqual(bad_days, [])

    @patch('seaice.datastore.seaicedatastore.read_datastore')
    def test_get_bad_days_for_missing_hemisphere(self, read_datastore):
        df = self._get_test_dataframe()
        read_datastore.return_value = df
        bad_days = sds.get_bad_days_for_hemisphere('N', self.fixture_filename)
        self.assertEqual(bad_days, [])
