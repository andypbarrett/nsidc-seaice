import copy
import datetime as dt
import os
import shutil
import yaml

import click

import seaice.nasateam as nt


DAILY_STATISTICS_DEFAULT_CONFIG = {
    'search_paths': nt.DEFAULT_SEA_ICE_PATHS,
    'interpolation_radius': 1,
    'extent_threshold': nt.EXTENT_THRESHOLD,
    'data_store': nt.DAILY_DATA_STORE_FILENAME,
    'pole_hole_value': nt.FLAGS['pole'],
    'missing_value': nt.FLAGS['missing'],
    'update_date_list': False,
    'regression_delta_km2': 500000,
    'eval_days': 10,
    'allow_missing_nrt': True
}
MONTHLY_STATISTICS_DEFAULT_CONFIG = copy.deepcopy(DAILY_STATISTICS_DEFAULT_CONFIG)
MONTHLY_STATISTICS_DEFAULT_CONFIG['data_store'] = nt.MONTHLY_DATA_STORE_FILENAME

DEFAULT_CONFIG_FILE = 'sea_ice_statistics.yaml'


def options(option_set_list):
    """ Custom decorator takes a list of click option groups to apply, returns
        function decorated with applicable options """
    def apply_common_options(function):
        option_groups = {
            'daily': [
                click.option('-s', '--start-date',
                             type=str,
                             default=str(dt.date.today() - dt.timedelta(5)),
                             help=('YYYY-MM-DD. Update data for a range of dates, starting here. '
                                   'Must be used with --end-date.  Defaults to t-5 days')),
                click.option('-e', '--end-date',
                             type=str,
                             default=str(dt.date.today() - dt.timedelta(1)),
                             help=('YYYY-MM-DD. Update data for a range of dates, ending here. '
                                   'Must be used with --start-date. Defaults to yesterday')),
            ],
            'base': [
                click.option('-h', '--hemisphere',
                             type=click.Choice(['N', 'S']), default='none',
                             help='Required. Hemisphere for which to update the data.'),
                click.option('-c', '--configfile',
                             type=str,
                             default=DEFAULT_CONFIG_FILE,
                             help='Path to YAML file containing config values.'),
            ],
            'regression': [
                click.option('--eval_days',
                             type=click.IntRange(5, 20),
                             default=DAILY_STATISTICS_DEFAULT_CONFIG['eval_days'],
                             help='Number (5-20) of prior days to consider when evaluating standard'
                                  ' deviations'),
                click.option('-rd', '--regression_delta_km2',
                             type=float,
                             default=DAILY_STATISTICS_DEFAULT_CONFIG['regression_delta_km2'],
                             help='Difference in km2 allowed between predicted measurement and '
                                  'actual from a simple linear regression over eval_days')
            ]}

        options_list = []
        for group, options in option_groups.items():
            if group in option_set_list:
                options_list.extend(options)

        for option in options_list:
            function = option(function)
        return function
    return apply_common_options


def _timestamp():
    return dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')


def archive_existing_datastore(ds_filename):
    """Rename file by postpending timestamp if the file exists"""
    if os.path.exists(ds_filename):
        filename, ext = os.path.splitext(ds_filename)
        new_filename = '{base}-{timestamp}{ext}'.format(base=ds_filename,
                                                        timestamp=_timestamp(),
                                                        ext=ext)
        shutil.copy(ds_filename, new_filename)


def load_config(configfile):
    try:
        with open(configfile) as fp:
            config = yaml.load(fp)
    except FileNotFoundError:
        if configfile == DEFAULT_CONFIG_FILE:
            config = {}
        else:
            raise

    # convert paths from being relative to the config file to absolute paths
    def resolve_path(path):
        if os.path.isabs(path):
            return path

        startdir = os.path.dirname(configfile)
        return os.path.realpath(os.path.join(startdir, path))

    if 'search_paths' in config.keys():
        config['search_paths'] = [resolve_path(path) for path in config['search_paths']]

    for i, _regional_mask in enumerate(config.get('regional_masks', [])):
        config['regional_masks'][i]['file'] = resolve_path(config['regional_masks'][i]['file'])

    for key in ['data_store', 'daily_data_store']:
        if key in config.keys():
            config[key] = resolve_path(config[key])

    return config
