import copy
import datetime as dt
import gzip
import logging
import logging.config
import os
import socket
import time

import yaml
from decorator import decorator


def log_command(logger, level_name='INFO'):
    """Decorator that prints function name/args/kwargs from a method in a useful
       log format. Returns function decorated without change/wrapped behavior
       other than printing to the log object.

       As this works with -functions- it's important to note in typical use that
       this will need to be the first decorator applied to a function (see usage).

    Arguments:

    logger - A python logging 'logger' object.

    Example Usage:

    import seaice.logging as seaicelogging
    logger = seaicelogging.init('project_name')
    @click_command()
    @other_click_decorators()
    @seaicelogging.log_command(logger)
    def foo(bar):
        print("Hi")
    """

    try:
        lvl = logging.getLevelName(level_name)
    except Exception:
        lvl = logging.INFO

    @decorator
    def logged_function(function, *args, **kwargs):
        logger.log(lvl, '{} called with {} : {} as '
                        'arguments'.format(function.__name__, args, kwargs))
        return function(*args, **kwargs)
    return logged_function


def log_duration(logger, level_name='DEBUG'):
    """Decorator that prints the time spent in a given function.

    Arguments:

    logger - A python logging 'logger' object.

    Example Usage:

    import seaice.logging as seaicelogging
    logger = seaicelogging.init('project_name')

    @log_duration(logger, 'INFO')
    def foo(bar):
        print("Hi")


    """
    try:
        lvl = logging.getLevelName(level_name)
    except Exception:
        lvl = logging.DEBUG

    @decorator
    def logged_function(function, *args, **kwargs):
        start = time.time()

        result = function(*args, **kwargs)

        logger.log(lvl,
                   'Finished {} in {:.5f} seconds.'.format(function.__name__, time.time() - start))
        return result

    return logged_function


def init(package_name):
    """Set up logging configuration for sea ice cli programs.

    by default the logging for sea ice commandline programs will output INFO
    level messages to both the console and to a rotating file in
    /share/logs/seaice/pacakge_name.log

    Arguments:

    package_name - Name of package importing the logging (sedna,
                   seaiceshapefiles, seaiceimages, etc.) This name will be used
                   as the default handler for the current package. It should be
                   the same name as your package, so that support libraries
                   that use __name__ will namespaced properly:
                   "package_name.supportname"


    usage:

    # in cli programs
    # ---------------
    import seaice.logging as seaicelogging

    log = seaicelogging.init('the-package-name')
    log.warn('something of a warning')

    # ^^^ would be handled by 'the-package-name' handler.

    # in other package modules (non-cli)
    import logging
    log = logging.getLogger(__name__)
    log.debug('debug level message')

    """
    config_path = os.path.join(os.path.dirname(__file__), 'ancillary', 'logging.yml')

    if os.path.exists(config_path):
        with open(config_path, 'r') as fp:
            config = yaml.safe_load(fp.read())

        config = _override_log_level(config)
        config = _override_root_log_level(config)
        config = _set_logger_name(config, package_name)
        config = _configure_log_file_handlers(config, package_name)

        logging.config.dictConfig(config)
        logging.getLogger(__name__).debug('loaded config %s', config)
    else:
        logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        logging.getLogger(__name__).warn('failed to load log config %s', config_path)

    return logging.getLogger(package_name)


def _override_log_level(in_config):
    """Override the default logging level for the package handler."""
    config = copy.deepcopy(in_config)
    log_level = os.getenv('LOG_LEVEL', None)
    if log_level:
        config['loggers']['package-name']['level'] = log_level

    return config


def _override_root_log_level(config_in):
    """Override the default logging level for the root handler."""
    config = copy.deepcopy(config_in)
    root_log_level = os.getenv('ROOT_LOG_LEVEL', None)
    if root_log_level:
        config['root']['level'] = root_log_level
    return config


def _set_logger_name(config_in, package_name):
    """Replace config yml's logger package-name with the real package name"""
    config = copy.deepcopy(config_in)
    config['loggers'][package_name] = config['loggers'].pop('package-name')
    return config


def _writeable_log_file(log_file):
    with open(log_file, 'a') as fp:  # noqa
        pass


def _configure_log_file_handlers(config_in, package_name):
    """Set the output log file, preferring the value in the environment variable LOG_FILE."""
    config = copy.deepcopy(config_in)
    log_file = os.getenv('LOG_FILE', None)

    if log_file is None:
        path, filename = os.path.split(config['handlers']['file_handler']['filename'])
        name, ext = os.path.splitext(filename)
        log_filename = '{}.{}{}'.format(package_name, socket.gethostname(), ext)
        log_file = os.path.join(path, log_filename)

    try:
        _writeable_log_file(log_file)  # noqa
        config['handlers']['file_handler']['filename'] = log_file
    except OSError as e:
        config['handlers'].pop('file_handler')
        config['loggers'][package_name]['handlers'].remove('file_handler')
        config['root']['handlers'].remove('file_handler')
        logging.getLogger(__name__).warn('********Failed to open log file at {},'
                                         ' logging to console only********'.format(log_file))
        logging.getLogger(__name__).exception(e)
    return config


class GzipRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Extends RotatingFileHandler to gzip rotated logs"""

    def _get_timestamp(self, fmt='%Y%m%d-%I:%M:%S'):
        return dt.datetime.today().strftime(fmt)

    def _get_archive_filename(self):
        timestamp = self._get_timestamp()
        return '{}.{}.gz'.format(self.baseFilename, timestamp)

    def doRollover(self):
        super().doRollover()

        old_logfile = self.baseFilename + '.1'
        with open(old_logfile) as log:
            with gzip.open(self._get_archive_filename(), 'wt') as ziplog:
                ziplog.writelines(log)

        os.remove(old_logfile)
