import datetime as dt

from unittest.mock import patch
import unittest

from ..remap import _substitute_variables, _turn_back_time


class test__substitute_variables(unittest.TestCase):

    def cfg(self):
        return {'step_by': 'days'}

    def test_no_substitution(self):
        cfg = self.cfg()
        pair = ('alpha', 'beta')
        expected = ('alpha', 'beta')
        actual = _substitute_variables(pair, cfg)
        self.assertEqual(actual, expected)

    @patch('seaice.filemapper.remap._today')
    def test_substitute_year(self, mock_today):
        cfg = self.cfg()
        mock_today.return_value = dt.date(2015, 1, 30)
        pair = ('alpha{year}', 'beta')
        expected = ('alpha2015', 'beta')
        actual = _substitute_variables(pair, cfg)
        self.assertEqual(actual, expected)

    @patch('seaice.filemapper.remap._today')
    def test_substitute_yyyymmdd(self, mock_today):
        cfg = self.cfg()
        mock_today.return_value = dt.date(2015, 1, 30)
        pair = ('alpha{yyyymmdd}delta', 'beta')
        expected = ('alpha20150129delta', 'beta')
        actual = _substitute_variables(pair, cfg)
        self.assertEqual(actual, expected)

    @patch('seaice.filemapper.remap._today')
    def test_substitute_funny_month_name_monthly(self, mock_today):
        cfg = self.cfg()
        cfg['step_by'] = 'months'
        mock_today.return_value = dt.date(2016, 12, 10)
        pair = ('alpha/{month}_{mon_abbrev}/delta', 'beta')
        expected = ('alpha/11_Nov/delta', 'beta')
        actual = _substitute_variables(pair, cfg)
        self.assertEqual(actual, expected)

    @patch('seaice.filemapper.remap._today')
    def test_substitute_short_month_name_monthly(self, mock_today):
        cfg = self.cfg()
        cfg['step_by'] = 'months'
        mock_today.return_value = dt.date(2017, 2, 3)
        pair = ('alpha/{month}_{mon_abbrev}/delta', 'beta')
        expected = ('alpha/01_Jan/delta', 'beta')
        actual = _substitute_variables(pair, cfg)
        self.assertEqual(actual, expected)


class Test__turn_back_time(unittest.TestCase):

    @patch('seaice.filemapper.remap._today')
    def test_expected_days_back(self, mock_today):
        mock_today.return_value = dt.date(2112, 3, 10)
        delta = {'days': -3}
        expected = dt.date(2112, 3, 10-3)
        actual = _turn_back_time(delta)
        self.assertEqual(actual, expected)

    @patch('seaice.filemapper.remap._today')
    def test_expected_months_back(self, mock_today):
        mock_today.return_value = dt.date(2112, 3, 10)
        delta = {'months': -1}
        expected = dt.date(2112, 2, 10)
        actual = _turn_back_time(delta)
        self.assertEqual(actual, expected)
