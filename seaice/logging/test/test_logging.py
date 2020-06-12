import logging
import socket
import unittest
from unittest.mock import patch

from ..logging import _configure_log_file_handlers, _set_logger_name
from ..logging import log_command, log_duration, _override_log_level, _override_root_log_level


class Test_log_command(unittest.TestCase):
    logger = logging.getLogger('test')

    @log_command(logger)
    def log_function(self, *args, **kwargs):
        """test docstring"""
        return '{} {}'.format(*args)

    @log_command(logger, 'DEBUG')
    def log_function_debug(self, *args, **kwargs):
        """test docstring"""
        return '{} {}'.format(*args)

    def test_retains_docstring(self):
        expected = 'test docstring'
        self.assertEqual(self.log_function.__doc__, expected)

    def test_function_called(self):
        expected = 'this that'
        self.assertEqual(self.log_function('this', 'that'), expected)

    def test_log_output(self):
        with self.assertLogs('test', level='INFO') as cm:
            self.log_function('this', 'that', foo='bar')
        expected = ['INFO:test:log_function called with '
                    '(<seaice.logging.test.test_logging.Test_log_command '
                    "testMethod=test_log_output>, 'this', 'that') : {'foo': 'bar'} as arguments"]
        self.assertEqual(cm.output, expected)

    def test_log_output_debug_level(self):
        with self.assertLogs('test', level='DEBUG') as cm:
            self.log_function_debug('this', 'that', foo='bar')
        expected = ['DEBUG:test:log_function_debug called with '
                    '(<seaice.logging.test.test_logging.Test_log_command '
                    "testMethod=test_log_output_debug_level>, 'this', 'that') "
                    ": {'foo': 'bar'} as arguments"]
        self.assertEqual(cm.output, expected)


class Test_log_duration(unittest.TestCase):
    logger = logging.getLogger('test')

    @log_duration(logger, 'INFO')
    def log_function(self, *args, **kwargs):
        """another test docstring"""
        return 'a return value string'

    def test_retains_docstring(self):
        expected = 'another test docstring'
        self.assertEqual(self.log_function.__doc__, expected)

    def test_function_called(self):
        expected = 'a return value string'
        self.assertEqual(self.log_function('this', 'that'), expected)

    def test_log_output(self):
        with self.assertLogs('test', level='INFO') as cm:
            self.log_function('this', 'that', foo='bar')
        expected = ['INFO:test:Finished log_function in \d+.\d+ seconds.']
        self.assertRegex(cm.output[0], expected[0])


class Test__override_log_level(unittest.TestCase):

    @patch('logging.os.getenv')
    def test_unchanged_if_envvar_unset(self, mockenv):
        config = {'loggers': {'package-name':
                              {'handlers': ['file_handler', 'console'],
                               'level': 'INFO',
                               'propagate': False}}}
        expected_level = config['loggers']['package-name']['level']
        mockenv.return_value = None

        actual_config = _override_log_level(config)
        self.assertEqual(actual_config['loggers'][
                         'package-name']['level'], expected_level)
        mockenv.assert_called_once_with('LOG_LEVEL', None)

    @patch('logging.os.getenv')
    def test_overrides_with_envvar(self, mockenv):
        config = {'loggers': {'package-name':
                              {'handlers': ['file_handler', 'console'],
                               'level': 'INFO',
                               'propagate': False}}}
        expected_level = 'CRITICAL'
        mockenv.return_value = 'CRITICAL'

        actual_config = _override_log_level(config)
        self.assertEqual(actual_config['loggers'][
                         'package-name']['level'], expected_level)
        mockenv.assert_called_once_with('LOG_LEVEL', None)


class Test__override_root_log_level(unittest.TestCase):

    @patch('logging.os.getenv')
    def test_unchanged_if_envvar_unset(self, mockenv):
        config = {'root': {'handlers': ['file_handler', 'console'],
                           'level': 'INFO'}}
        expected_level = config['root']['level']
        mockenv.return_value = None

        actual_config = _override_root_log_level(config)
        self.assertEqual(actual_config['root']['level'], expected_level)
        mockenv.assert_called_once_with('ROOT_LOG_LEVEL', None)

    @patch('logging.os.getenv')
    def test_overrides_with_envvar(self, mockenv):
        config = {'root': {'handlers': ['file_handler', 'console'],
                           'level': 'INFO'}}
        expected_level = 'CRITICAL'
        mockenv.return_value = 'CRITICAL'

        actual_config = _override_root_log_level(config)
        self.assertEqual(actual_config['root']['level'], expected_level)
        mockenv.assert_called_once_with('ROOT_LOG_LEVEL', None)


class Test__set_logger_name(unittest.TestCase):

    def test_sets_logger_name(self):
        config = {'loggers': {'package-name':
                              {'handlers': ['file_handler', 'console'],
                               'level': 'INFO',
                               'propagate': False}}}
        expected_logger_name = 'testcase'

        actual_config = _set_logger_name(config, 'testcase')
        self.assertEqual(actual_config['loggers'][expected_logger_name],
                         config['loggers']['package-name'])


class Test__configure_log_file_handlers(unittest.TestCase):

    def setUp(self):
        self.config = {'root': {'handlers': ['file_handler', 'console']},
                       'loggers': {'packagename': {'handlers': ['file_handler', 'console']}},
                       'handlers': {'file_handler': {'filename': 'pathto/unchanged.log'}}}

    @patch('seaice.logging.logging._writeable_log_file')
    @patch('logging.os.getenv')
    def test_defaults_to_package_name_if_not_overridden(self, mockenv, mockwriteable):
        config = self.config
        mockenv.return_value = None
        mockwriteable.return_value = None

        expected = 'pathto/packagename.{}.log'.format(socket.gethostname())
        actual = _configure_log_file_handlers(config, 'packagename')
        self.assertEqual(actual['handlers']['file_handler'][
            'filename'], expected)

    @patch('seaice.logging.logging._writeable_log_file')
    @patch('logging.os.getenv')
    def test_removes_file_handlers_if_filepath_unwritable(self, mockenv, mockwriteable):
        config = self.config
        mockwriteable.side_effect = OSError()
        config['handlers']['file_handler']['filename'] = 'pathto/seaice.log'
        mockenv.return_value = 'totally-fake-logfile.log'
        actual = _configure_log_file_handlers(config, 'packagename')

        expected = {'root': {'handlers': ['console']},
                    'loggers': {'packagename': {'handlers': ['console']}},
                    'handlers': {}}

        self.assertDictEqual(actual, expected)

    @patch('seaice.logging.logging._writeable_log_file')
    @patch('logging.os.getenv')
    def test_overrides_with_environment(self, mockenv, mockwriteable):
        config = self.config
        mockwriteable.return_value = True
        config['handlers']['file_handler']['filename'] = 'pathto/seaice.log'
        mockenv.return_value = 'totally-fake-logfile.log'

        expected = 'totally-fake-logfile.log'
        actual = _configure_log_file_handlers(config, 'packagename')
        self.assertEqual(actual['handlers']['file_handler'][
                         'filename'], expected)
        mockenv.assert_called_once_with('LOG_FILE', None)
