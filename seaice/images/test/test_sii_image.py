import copy
import datetime as dt
import unittest
from unittest.mock import patch

from click.testing import CliRunner

import seaice.images.cli.sii_image as sii_image


class Test_sii_image(unittest.TestCase):

    def _basic_cmd_line_args(self):
        return ['-h', 'N', '-y', '1995', '-m', '5', '-d', '15']

    @patch('seaice.images.api.ice_image')
    def test_actually_calls_api(self, conc_mock):
        """This test fails if there's an exception in calling
        seaice.images.cli.sii_image.
        """
        env = {'LOG_FILE': 'local_logfile.log'}
        cmd_line_args = self._basic_cmd_line_args()

        runner = CliRunner()
        result = runner.invoke(sii_image.sii_image, cmd_line_args, env=env)
        self.assertEqual(result.exception, None)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_expected_kwargs(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)
        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': None,
                           'blue_marble': False,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'image_type': 'concentration',
                           'hires': False,
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_updated_kwargs(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        cmd_line_args.append('--hires')
        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)
        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': None,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'image_type': 'concentration',
                           'hires': True,
                           'flatten': False,
                           'blue_marble': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_and_fills_kwargs_correctly(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        cmd_line_args.extend(['-o', 'output_file.png'])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)
        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': 'output_file.png',
                           'blue_marble': False,
                           'config_filename': None,
                           'temporality': 'daily',
                           'flatten': False,
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'image_type': 'concentration',
                           'hires': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_image_type_extent(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        cmd_line_args.extend(['--extent'])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': None,
                           'blue_marble': False,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'image_type': 'extent',
                           'flatten': False,
                           'hires': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_image_type_concentration(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = ['-h', 'N', '-y', '1995', '-m', '5',
                         '-d', '15', '-s', '3',
                         '--config_filename', '/a/config/file.yml',
                         '-o', 'output_file.png', '--concentration']

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': 'output_file.png',
                           'blue_marble': False,
                           'config_filename': '/a/config/file.yml',
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 3.0},
                           'hires': False,
                           'image_type': 'concentration',
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_latest_date(self, img_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = ['-h', 'N', '--config_filename', '/a/config/file.yml',
                         '-o', 'output_file.png', '--concentration',
                         '--latest', '1']

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        latest_date = dt.date.today() - dt.timedelta(days=1)

        expected_kwargs = {'hemisphere': 'N',
                           'date': latest_date,
                           'output': 'output_file.png',
                           'blue_marble': False,
                           'config_filename': '/a/config/file.yml',
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'image_type': 'concentration',
                           'flatten': False,
                           'hires': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}
        img_mock.assert_called_with(**expected_kwargs)

    @patch('os.path.isdir')
    @patch('seaice.images.api.ice_image')
    def test_calls_api_with_date_range(self, conc_mock, mock_isdir):
        mock_isdir.return_value = True
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = ['-h', 'N']
        cmd_line_args.extend(['-o', 'output_dir', '--range', '20111211,20111212'])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'output': 'output_dir',
                           'blue_marble': False,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'hires': False,
                           'image_type': 'concentration',
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}

        kwargs1 = copy.deepcopy(expected_kwargs)
        kwargs1['date'] = dt.date(2011, 12, 11)

        kwargs2 = copy.deepcopy(expected_kwargs)
        kwargs2['date'] = dt.date(2011, 12, 12)

        conc_mock.assert_any_call(**kwargs1)
        conc_mock.assert_any_call(**kwargs2)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_blue_marble_extent(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        cmd_line_args.extend(['-o', 'output_dir', '--blue_marble', '--extent'])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': 'output_dir',
                           'blue_marble': True,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'hires': False,
                           'image_type': 'extent',
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}

        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_blue_marble_conc(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = self._basic_cmd_line_args()
        cmd_line_args.extend(['-o', 'output_dir', '--blue_marble', '--concentration'])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(1995, 5, 15),
                           'output': 'output_dir',
                           'blue_marble': True,
                           'config_filename': None,
                           'temporality': 'daily',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'hires': False,
                           'image_type': 'concentration',
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': None,
                           'trend_clipping_threshold': 100}

        conc_mock.assert_called_with(**expected_kwargs)

    @patch('seaice.images.api.ice_image')
    def test_calls_api_trend_with_custom_start_year(self, conc_mock):
        runner = CliRunner()
        env = {'LOG_FILE': 'local_logfile.log'}

        cmd_line_args = ['-h', 'N', '-y', '2018', '-m', '1', '--monthly']
        cmd_line_args.extend(['-o', 'output_dir', '--trend', '--trend-start-year', 2010])

        runner.invoke(sii_image.sii_image, cmd_line_args, env=env)

        expected_kwargs = {'hemisphere': 'N',
                           'date': dt.date(2018, 1, 1),
                           'output': 'output_dir',
                           'blue_marble': False,
                           'config_filename': None,
                           'temporality': 'monthly',
                           'allow_bad_data': False,
                           'canvas': {'scale': 1.0},
                           'hires': False,
                           'image_type': 'trend',
                           'flatten': False,
                           'year_range': (1981, 2010),
                           'values': {},
                           'overwrite': True,
                           'trend_start_year': 2010,
                           'trend_clipping_threshold': 100}

        conc_mock.assert_called_with(**expected_kwargs)


class Test_YearRange(unittest.TestCase):
    def test_converts_string_to_tuple(self):
        actual = sii_image.YearRange().convert('1981,2010', None, None)
        self.assertEqual(actual, (1981, 2010))

    def test_sorts_out_of_order_years(self):
        actual = sii_image.YearRange().convert('2010,1981', None, None)
        self.assertEqual(actual, (1981, 2010))

    def test_raises_error_if_range_in_wrong_format(self):
        with self.assertRaises(Exception):
            sii_image.YearRange().convert('1981-2010', None, None)
