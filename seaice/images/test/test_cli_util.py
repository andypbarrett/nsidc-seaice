import copy
import datetime as dt
import unittest

from seaice.images.errors import SeaIceImagesBadCommandLineArguments
from .util import mock_today
import seaice.images.cli.cli_util as cli_util
import seaice.nasateam as nt


class Test_validate_command_line_options(unittest.TestCase):

    def _valid_daily_config(self):
        return {
            'hemi': 'N',
            'year': 2015,
            'month': 5,
            'day': 20,
            'temporality': 'daily',
            'latest': None,
            'all': False,
            'year_range': (1981, 2010),
            'values': {}
        }

    def _valid_monthly_config(self):
        cfg = self._valid_daily_config()
        cfg.pop('day')
        cfg['temporality'] = 'monthly'
        return cfg

    def test_needs_hemisphere_argument(self):
        cfg = self._valid_daily_config()
        cfg['hemi'] = None
        with self.assertRaises(SeaIceImagesBadCommandLineArguments) as cm:
            cli_util.validate_command_line_options(cfg)
        self.assertRegex(str(cm.exception), 'must provide a hemi')

    def test_needs_year_argument(self):
        cfg = self._valid_daily_config()
        cfg['year'] = None
        with self.assertRaises(SeaIceImagesBadCommandLineArguments) as cm:
            cli_util.validate_command_line_options(cfg)
        self.assertRegex(str(cm.exception), 'must provide a year')

    def test_needs_month_argument(self):
        cfg = self._valid_daily_config()
        cfg['month'] = None
        with self.assertRaises(SeaIceImagesBadCommandLineArguments) as cm:
            cli_util.validate_command_line_options(cfg)
        self.assertRegex(str(cm.exception), 'must provide a month')

    def test_daily_image_needs_day_key(self):
        cfg = self._valid_daily_config()
        cfg['day'] = None
        with self.assertRaises(SeaIceImagesBadCommandLineArguments) as cm:
            cli_util.validate_command_line_options(cfg)
        self.assertRegex(str(cm.exception), 'must provide a day for a daily image')

    def test_valid_daily_config_is_unchanged(self):
        cfg = self._valid_daily_config()
        expected = copy.deepcopy(cfg)
        actual = cli_util.validate_command_line_options(cfg)
        self.assertEqual(expected, actual)

    def test_monthly_add_a_default_day_value(self):
        cfg = self._valid_monthly_config()
        expected = copy.deepcopy(cfg)
        expected['day'] = 1
        actual = cli_util.validate_command_line_options(cfg)
        self.assertEqual(expected, actual)

    def test_latest_does_not_need_date_keys(self):
        cfg = self._valid_daily_config()
        cfg['latest'] = True
        for key in ['day', 'year', 'month']:
            cfg.pop(key)
        expected = copy.deepcopy(cfg)
        actual = cli_util.validate_command_line_options(cfg)
        self.assertEqual(expected, actual)

    def test_raises_error_with_conflicting_args(self):
        cfg = self._valid_daily_config()
        cfg['latest'] = True
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_works_if_anomaly_has_year_range(self):
        cfg = self._valid_daily_config()
        cfg['image_type'] = 'anomaly'
        expected = copy.deepcopy(cfg)
        actual = cli_util.validate_command_line_options(cfg)
        self.assertEqual(expected, actual)

    def test_raises_error_if_anomaly_has_no_year_range(self):
        cfg = self._valid_daily_config()
        cfg['image_type'] = 'anomaly'
        cfg['year_range'] = None
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_raises_error_if_bad_output_with_all(self):
        cfg = self._valid_daily_config()
        cfg['all'] = True
        cfg['output'] = '/not/an/existing/dir'
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_raises_error_if_bad_output_with_latest(self):
        cfg = self._valid_daily_config()
        cfg['latest'] = 1
        cfg['output'] = '/not/an/existing/dir'
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_raises_error_if_bad_output_with_range(self):
        cfg = self._valid_daily_config()
        cfg['range'] = True
        cfg['output'] = '/not/an/existing/dir'
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_raises_error_if_bad_output_with_both_hemispheres(self):
        cfg = self._valid_daily_config()
        cfg['hemi'] = 'N,S'
        cfg['output'] = 'test.png'
        with self.assertRaises(SeaIceImagesBadCommandLineArguments):
            cli_util.validate_command_line_options(cfg)

    def test_raises_error_if_bad_image_type_with_blue_marble(self):
        cfg = self._valid_daily_config()
        cfg['blue_marble'] = True
        for image_type in ('anomaly', 'trend'):
            cfg['image_type'] = image_type
            regex = ('The --blue_marble option is not compatible '
                     'with the {} image type'.format(image_type))
            with self.assertRaisesRegexp(SeaIceImagesBadCommandLineArguments, regex):
                cli_util.validate_command_line_options(cfg)

    def test_works_with_all_and_other_temporal_options(self):
        cfg = self._valid_daily_config()
        cfg['all'] = True
        expected = copy.deepcopy(cfg)
        actual = cli_util.validate_command_line_options(cfg)
        self.assertEqual(expected, actual)


class Test__get_latest_date(unittest.TestCase):
    def test_returns_daily_latest_date(self):
        expected = [dt.date.today() - dt.timedelta(days=1)]
        actual = cli_util._get_latest_date('D')
        self.assertEqual(expected, actual)

    def test_returns_monthly_latest_date(self):
        today = dt.date.today()
        expected = today.replace(day=1) - dt.timedelta(days=1)
        actual = cli_util._get_latest_date('M')
        self.assertEqual(expected.month, actual[0].month)
        self.assertEqual(expected.year, actual[0].year)


class Test__get_latest_n_dates(unittest.TestCase):
    @mock_today(2014, 12, 1, 'seaice.images.cli.cli_util')
    def test_returns_daily_latest_two_dates(self):
        expected = [dt.date(2014, 11, 29),
                    dt.date(2014, 11, 30)]
        actual = cli_util._get_latest_n_dates('D', 2)

        self.assertEqual(expected, actual)

    @mock_today(2014, 12, 1, 'seaice.images.cli.cli_util')
    def test_returns_monthly_latest_two_dates(self):
        expected = [dt.date(2014, 10, 1),
                    dt.date(2014, 11, 1)]
        actual = cli_util._get_latest_n_dates('M', 2)

        self.assertEqual(expected, actual)


class Test__get_date_range(unittest.TestCase):
    def test_returns_daily_date_range(self):
        start_date = dt.date(2010, 1, 1)
        end_date = dt.date(2010, 1, 3)
        expected = [start_date,
                    dt.date(2010, 1, 2),
                    end_date]
        actual = cli_util._get_date_range(start_date, end_date, 'D')
        self.assertEqual(expected, actual)

    def test_returns_monthly_date_range(self):
        start_date = dt.date(2010, 1, 31)
        end_date = dt.date(2010, 3, 31)
        # Note: this func returns the last day of each
        # month for the monthly frequency.
        expected = [start_date,
                    dt.date(2010, 2, 28),
                    end_date]
        actual = cli_util._get_date_range(start_date, end_date, 'M')
        self.assertEqual(expected, actual)


class Test_get_dates(unittest.TestCase):
    def test_returns_single_date_if_y_m_d_passed(self):
        cfg = {'year': 2010, 'month': 1, 'day': 2}
        expected = [dt.date(**cfg)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    def test_returns_range_if_range_passed(self):
        start_date = dt.date(2010, 1, 1)
        end_date = dt.date(2010, 1, 3)
        cfg = {'range': (start_date, end_date),
               'temporality': 'daily'}
        expected = [start_date,
                    dt.date(2010, 1, 2),
                    end_date]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    def test_returns_latest_date_if_latest_passed(self):
        cfg = {'latest': 1,
               'temporality': 'daily'}
        expected = [dt.date.today() - dt.timedelta(days=1)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    @mock_today(2016, 11, 2, 'seaice.images.cli.cli_util')
    def test_returns_all_dates_if_all_passed(self):
        cfg = {'all': True,
               'temporality': 'daily',
               'range': None}
        expected_first_date = nt.BEGINNING_OF_SATELLITE_ERA
        expected_last_date = dt.date(2016, 11, 1)
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected_first_date, actual[0])
        self.assertEqual(expected_last_date, actual[-1])

    @mock_today(2016, 11, 2, 'seaice.images.cli.cli_util')
    def test_returns_all_months_if_all_passed(self):
        cfg = {'all': True,
               'temporality': 'monthly',
               'range': None}
        expected_first_month = nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY
        expected_last_month = dt.date(2016, 10, 1)
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected_first_month, actual[0])
        self.assertEqual(expected_last_month, actual[-1])

    @mock_today(2016, 11, 2, 'seaice.images.cli.cli_util')
    def test_returns_all_years_with_month_if_all_passed_with_month(self):
        SEPTEMBER = 9
        cfg = {'all': True,
               'temporality': 'monthly',
               'month': SEPTEMBER,
               'range': None}
        expected_first_month = dt.date(1979, 9, 1)
        expected_last_month = dt.date(2016, 9, 1)

        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected_first_month, actual[0])
        self.assertEqual(expected_last_month, actual[-1])

        for date in actual:
            self.assertEqual(date.month, SEPTEMBER)

    @mock_today(2016, 11, 2, 'seaice.images.cli.cli_util')
    def test_returns_all_days_from_year_if_all_passed_with_days(self):
        cfg = {'all': True,
               'temporality': 'daily',
               'year': 2015,
               'range': None}
        expected_first_day = dt.date(2015, 1, 1)
        expected_last_day = dt.date(2015, 12, 31)

        actual = cli_util.get_dates(cfg)

        self.assertEqual(len(actual), 365)
        self.assertEqual(expected_first_day, actual[0])
        self.assertEqual(expected_last_day, actual[-1])

        for date in actual:
            self.assertEqual(date.year, 2015)

    @mock_today(2014, 12, 1, 'seaice.images.cli.cli_util')
    def test_returns_latest_two_dates(self):
        cfg = {'latest': 2,
               'temporality': 'daily'}
        expected = [dt.date(2014, 11, 29),
                    dt.date(2014, 11, 30)]
        actual = cli_util.get_dates(cfg)

        self.assertEqual(actual, expected)

    @mock_today(2014, 12, 31, 'seaice.images.cli.cli_util')
    def test_returns_first_day_from_latest_two_months(self):
        cfg = {'latest': 2,
               'temporality': 'monthly'}
        expected = [dt.date(2014, 10, 1),
                    dt.date(2014, 11, 1)]
        actual = cli_util.get_dates(cfg)

        self.assertEqual(actual, expected)

    @mock_today(2015, 5, 5, 'seaice.images.cli.cli_util')
    def test_returns_adjusted_range_if_range_ending_in_current_month_passed_daily(self):
        start_date = dt.date(2015, 4, 29)
        end_date = dt.date(2015, 5, 2)
        cfg = {'range': (start_date, end_date),
               'temporality': 'daily'}
        expected = [dt.date(2015, 4, 29),
                    dt.date(2015, 4, 30),
                    dt.date(2015, 5, 1),
                    dt.date(2015, 5, 2)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    @mock_today(2015, 5, 5, 'seaice.images.cli.cli_util')
    def test_returns_adjusted_range_if_range_ending_today_passed_daily(self):
        start_date = dt.date(2015, 4, 29)
        end_date = dt.date(2015, 5, 5)
        cfg = {'range': (start_date, end_date),
               'temporality': 'daily'}
        expected = [dt.date(2015, 4, 29),
                    dt.date(2015, 4, 30),
                    dt.date(2015, 5, 1),
                    dt.date(2015, 5, 2),
                    dt.date(2015, 5, 3),
                    dt.date(2015, 5, 4)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    @mock_today(2015, 5, 5, 'seaice.images.cli.cli_util')
    def test_returns_adjusted_range_if_range_ending_in_the_future_passed_daily(self):
        start_date = dt.date(2015, 4, 29)
        end_date = dt.date(2015, 5, 10)
        cfg = {'range': (start_date, end_date),
               'temporality': 'daily'}
        expected = [dt.date(2015, 4, 29),
                    dt.date(2015, 4, 30),
                    dt.date(2015, 5, 1),
                    dt.date(2015, 5, 2),
                    dt.date(2015, 5, 3),
                    dt.date(2015, 5, 4)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)

    @mock_today(2015, 5, 5, 'seaice.images.cli.cli_util')
    def test_returns_adjusted_range_if_range_ending_in_current_month_passed_monthly(self):
        start_date = dt.date(2015, 4, 29)
        end_date = dt.date(2015, 5, 2)
        cfg = {'range': (start_date, end_date),
               'temporality': 'monthly'}
        expected = [dt.date(2015, 4, 30)]
        actual = cli_util.get_dates(cfg)
        self.assertEqual(expected, actual)
