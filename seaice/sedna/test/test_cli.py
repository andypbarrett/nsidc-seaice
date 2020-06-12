import datetime as dt
import tempfile
import os
import unittest
from unittest.mock import patch

from seaice.sedna.cli.util import archive_existing_datastore
from seaice.sedna.cli.initialize_sea_ice_statistics_daily import _get_last_date_with_finalized_data
from seaice.sedna.errors import SednaError


class Test_archive_existing_datastore(unittest.TestCase):

    @patch('seaice.sedna.cli.util._timestamp')
    def test_renames_datastore(self, timestamp_mock):
        timestamp = 'timestampvalue'
        timestamp_mock.return_value = timestamp

        with tempfile.TemporaryDirectory() as tdir:
            tfp, tfile = tempfile.mkstemp(dir=tdir)

            archive_existing_datastore(tfile)

            name, ext = os.path.splitext(tfile)

            self.assertTrue(os.path.exists(name + '-' + timestamp + ext))

    @patch('seaice.sedna.cli.util.os.path.exists')
    def test_ignores_missing_datastore(self, exist_mock):
        exist_mock.return_value = False

        archive_existing_datastore('./nope')

        exist_mock.assert_called_with('./nope')


class Test__get_last_date_with_finalized_data(unittest.TestCase):
    @patch('seaice.sedna.cli.initialize_sea_ice_statistics_daily.os.walk')
    def test_returns_last_date_if_all_final(self, mock_walk):
        mock_walk.return_value = [('/foo', ('bar',), ('nt_20150101_f17_v1.1_n.bin',
                                                      'nt_20150103_f17_v1.1_n.bin',
                                                      'nt_20150105_f17_v1.1_n.bin',
                                                      'nt_20150102_f17_v1.1_n.bin',
                                                      'nt_20150104_f17_v1.1_n.bin'))]

        expected = dt.date(2015, 1, 5)

        actual = _get_last_date_with_finalized_data()

        self.assertEqual(actual, expected)

    @patch('seaice.sedna.cli.initialize_sea_ice_statistics_daily.os.walk')
    def test_returns_last_date_if_monthly_exists_all_final(self, mock_walk):
        mock_walk.return_value = [('/foo', ('bar',), ('nt_20150101_f17_v1.1_n.bin',
                                                      'nt_20150102_f17_v1.1_n.bin',
                                                      'nt_20150105_f17_v1.1_n.bin',
                                                      'nt_201506_f17_v1.1_n.bin',
                                                      'nt_20150102_f17_v1.1_n.bin'))]

        expected = dt.date(2015, 1, 5)

        actual = _get_last_date_with_finalized_data()

        self.assertEqual(actual, expected)

    @patch('seaice.sedna.cli.initialize_sea_ice_statistics_daily.os.walk')
    def test_returns_none_if_no_daily_exists(self, mock_walk):
        mock_walk.return_value = [('/foo', ('bar',), ('nt_201501_f17_v1.1_n.bin',
                                                      'nt_201502_f17_v1.1_n.bin',
                                                      'nt_201505_f17_v1.1_n.bin',
                                                      'nt_201506_f17_v1.1_n.bin',
                                                      'nt_201507_f17_v1.1_n.bin'))]

        self.assertRaises(SednaError, _get_last_date_with_finalized_data)
