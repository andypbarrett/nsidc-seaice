# Software to move seaice output files into files named for the old website.
import calendar as cal
import datetime as dt
import os
import shutil

import click
import yaml
from dateutil.relativedelta import relativedelta

import seaice.nasateam as nt
import seaice.logging as seaicelogging


log = seaicelogging.init('seaice.filemapper')

DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'ancillary', 'mapper.yml')


@click.command()
@click.option('-d', '--daily', 'temporality', flag_value='daily', default=True,
              help='Prepare daily files for website')
@click.option('-m', '--monthly', 'temporality', flag_value='monthly',
              help='Prepare monthly files for website')
@click.argument('config_filename', default=DEFAULT_CONFIG_FILE)
@seaicelogging.log_command(log)
def remap(**kwargs):
    """a commandline interface to copy seaice output files to the appropriate filenames to
    be displayed on the seiace index website.

    \b
    CONFIG_FILENAME:

      yaml configuration describing the source file patterns and target output
      filenames to be transfered.

      Default value [./ancillary/mapper.yml] a locally defined configuration
      file stored in the package that correctly copies files for standard
      processing.

    \b
    configuration description:

    \b The configuration file has at least one of the top level keys: ['daily',
    'monthly'] that is selected by the value of the input temporailty flag.

    \b Under these are subkeys: ['source_root', 'destination_root', 'files']

    \b source_root: root directory of the input file pattern

    \b destination_root: root directory of the output filename

    \b files: is a list of dicts, where each dict's key is the source file
    pattern and the value is the output filename.

    \b the source file is found by joining the source_root and files[i].key and
    the file is copied to the path created by joining destination_root with
    files[i].value

    """
    log.info('remap called with kwargs: %s', kwargs)

    cfg = yaml.safe_load(open(kwargs['config_filename'], 'r')).pop(kwargs['temporality'])
    log.debug('remapping files with config[%s]: %s', kwargs['temporality'], cfg)

    filled_file_pairs = [_substitute_variables(pair, cfg) for pair in _process_cfg(cfg)]

    [_copy_files(pair) for pair in filled_file_pairs]


def _copy_files(pair):
    "Copy from source to dest raising error if source doesn't exist"
    src, dest = pair
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        shutil.copyfile(src, dest)
        log.info('copied {} => {}'.format(src, dest))
    except FileNotFoundError as e:
        log.exception('Source File: %s not found.', src)
        raise
    except PermissionError as e:
        log.exception('Permission denied writing copying to %s.', dest)
        raise
    except Exception as e:
        log.exception('caught exception: %s', e)
        raise


def _format_dict(_date):
    return {'year': _date.year,
            'yyyymmdd': _date.strftime('%Y%m%d'),
            'yyyymm': _date.strftime('%Y%m'),
            'mon_abbrev': cal.month_abbr[_date.month],
            'month': _date.strftime('%m'),
            'version_string': nt.VERSION_STRING}


def _process_cfg(cfg):
    """ turn the input config dictionary into a list of tuples (sourcepattern, destinationfile) """
    return [(os.path.join(cfg['source_root'], key), os.path.join(cfg['destination_root'], value))
            for dict_ in cfg['files']
            for (key, value) in dict_.items()]


def _substitute_variables(pair, cfg):
    src, dest = pair
    delta = {cfg['step_by']: -1}
    search_date = _turn_back_time(delta)
    format_dict = _format_dict(search_date)
    src = src.format(**format_dict)

    return (src, dest)


def _today():
    return dt.date.today()


def _turn_back_time(delta):
    today = _today()
    return today + relativedelta(**delta)


if __name__ == '__main__':
    remap()
