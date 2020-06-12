from itertools import product
from multiprocessing import Pool
from calendar import monthrange
import copy
import datetime as dt
import pprint
import traceback

import click
import pandas as pd

import seaice.nasateam as nt
import seaice.logging as seaicelogging
from seaice.data import SeaIceDataNoData
from seaice import version_flag
from ..daily_median import daily_median
from ..monthly_median_polyline import monthly_median_polyline
from ..monthly_polyline import monthly_polyline
from ..monthly_polygon import monthly_polygon
from ..errors import SeaIceShapefilesError

log = seaicelogging.init('seaice.shapefiles')

TODAY = dt.date.today()

DEFAULTS = {
    'extent_threshold': nt.EXTENT_THRESHOLD,
    'pole_hole': nt.FLAGS['pole'],
    'output_dir': '.',
    'version_str': nt.VERSION_STRING,
    'search_paths': nt.DEFAULT_SEA_ICE_PATHS
}


class DateRangeType(click.ParamType):
    name = 'DateRange'

    def __init__(self, date_fmt='%Y-%m-%d'):
        self.date_fmt = date_fmt

    def convert(self, value, param, ctx):
        try:
            start, end = value.split(',')
            start = dt.datetime.strptime(start, self.date_fmt).date()
            end = dt.datetime.strptime(end, self.date_fmt).date()
            if start >= end:
                self.fail('The given start date of {} does not come before'
                          ' the end date {}.'.format(start.strftime(self.date_fmt),
                                                     end.strftime(self.date_fmt)))
            return [start, end]
        except Exception as e:
            self.fail('Failure parsing {}. {}'.format(value, e))


DateRange = DateRangeType()


@click.command()
@version_flag
@click.option('--daily', is_flag=True, default=False,
              help=('Create daily shapefiles. Not compatible with --monthly.'))
@click.option('--monthly', is_flag=True, default=False,
              help=('Create monthly shapefiles. Not compatible with --daily.'))
@click.option('--polygon', is_flag=True, default=False,
              help=('Create polygon shapefiles. Not compatible with --polyline.'))
@click.option('--polyline', is_flag=True, default=False,
              help=('Create polyline shapefiles. Not compatible with --polygon.'))
@click.option('--median', is_flag=True, default=False,
              help=('Create shapefiles for median data from the climatology.'))
@click.option('--range', default=','.join([str(y) for y in nt.DEFAULT_CLIMATOLOGY_YEARS]),
              help=('YYYY,YYYY. Specify a range of years from which to calculate the median. '
                    'Only has effect when used with --median. Defaults to '
                    'nt.DEFAULT_CLIMATOLOGY_YEARS.'))
@click.option('-h', '--hemi', type=click.Choice(['N', 'S', 'N,S', 'S,N']), default='N,S',
              help=('Hemisphere. If none is specified, create shapefiles for both hemispheres.'))
@click.option('--all', is_flag=True,
              help=('(temporal) Create a shapefile for every valid period starting from '
                    'nt.BEGINNING_OF_SATELLITE_ERA.'))
@click.option('--latest', type=int,
              help=('(temporal) Create shapefiles for the INTEGER most recent periods. If no '
                    'temporal option is used, --latest 1 will be used.'))
@click.option('-y', '--year', type=int,
              help=('(temporal) YYYY. Year. Not compatible with --median, as that implies a range '
                    'of years.'))
@click.option('-m', '--month', type=int,
              help=('(temporal) MM. Month.'))
@click.option('-d', '--day', type=int,
              help=('(temporal) DD. Day of the month.'))
@click.option('-doy', '--dayofyear', type=int,
              help=('(temporal) DDD. Day of year. When used with --median, specifies a '
                    'day of the year for a climatology median; otherwise, can be used to '
                    'create a shapefile for the given --year. Can be used instead of --month.'))
@click.option('-o', '--output_dir', type=click.Path(resolve_path=True, file_okay=False),
              help=('The root directory in which to save the created .zip. Defaults to the '
                    'current directory. Shapefiles are the created in subdirectories matching their'
                    'archival locations. (subdirectory expansion can be overridden by using the'
                    '--flatten flag)'))
@click.option('-f', '--flatten', is_flag=True, default=False,
              help='Create the shapefile without including the archive directory structure.')
@click.option('-s', '--search_paths', type=str,
              help=('List of paths to sea ice data. Defaults to '
                    'nt.DEFAULT_SEA_ICE_PATHS ({})'.format(','.join(nt.DEFAULT_SEA_ICE_PATHS))))
@click.option('-v', '--version_str', type=str,
              help=('Version string to include in the shapefile\'s name. Defaults to '
                    'nt.VERSION_STRING ({})'.format(nt.VERSION_STRING)))
@click.option('-e', '--extent_threshold', type=float,
              help=('The minimum concentration percentage which should be counted as part of the '
                    'extent. Defaults to nt.EXTENT_THRESHOLD ({}).').format(nt.EXTENT_THRESHOLD))
@click.option('-p', '--pole_hole', type=int,
              help=('The pole hole flag value. Data cannot be collected here, but should '
                    'still be counted as part of the extent. Defaults to '
                    'nt.FLAGS[\'pole\'] ({}).').format(nt.FLAGS['pole']))
@click.option('--debug_config', is_flag=True,
              help=('Instead of generating shapefiles, print the configuration '
                    'parsed from these CLI options and exit.'))
@click.option('--date-range', type=DateRange, default=None,
              help='Creates monthly shapefiles for every month in the given range.'
              ' Dates should be formatted as YYYY-MM-DD and separated by a comma (e.g.,'
              ' YYYY-MM-DD,YYYY-MM-DD). Not compatible with --median, -y, -m, -d, --latest, --all.')
@seaicelogging.log_command(log)
def cli(**kwargs):
    """Sea Ice Index Shapefiles

    Create one or more Shapefiles for sea ice extent. A Shapefile is a .zip file
    containing a .zip and other related files.

    The full documentation for the available options is shown below, after the
    usage examples.

    Options noted with "(temporal)" are time-related parameters which can be
    used to restrict the time range of interest to create fewer shapefiles.

    For climatology shapefiles (--median option supplied), if no temporal
    options are supplied, a default of "--all" is appended to the request, and
    shapefiles for all days of year (--daily) or all months (--monthly) are
    generated.

    For other shapefiles, when no temporal options are supplied, "--latest 1"
    will be used as the default, which will create a shapefile for yesterday
    (--daily) or last month (--monthly).

    If the temporal options given do not narrow the time range to a single
    point, multiple shapefiles will be created. For example,

        sii_shp --monthly --polygon -y 2013

    creates 12 monthly extent polygon shapefiles, one for each month in 2013. To
    create only the polygon shapefile for July 2013:

        sii_shp --monthly --polygon -y 2013 -m 7

    Usage examples:

    - Generate climatology median day of year shapefiles for a single day of the
      year:

        sii_shp --daily --median --polyline -doy 127

    - Generate climatology median day of year shapefiles for all days:

        sii_shp --daily --median --polyline --all
        sii_shp --daily --median --polyline

    - Generate monthly climatology median files for all 12 months:

        sii_shp --monthly --median --polyline --all
        sii_shp --monthly --median --polyline

    - Generate monthly sea ice extent polyline shapefiles for every December:

        sii_shp --monthly --polyline -m 12

    - Generate all monthly climatology median files using 1986-2015 as the
      climatology range:

        sii_shp --monthly --median --polyline --all --range 1986,2015
        sii_shp --monthly --median --polyline --range 1986,2015

    - Generate last month's polygons:

        sii_shp --monthly --polygon --latest=1
        sii_shp --monthly --polygon

    - Generate polygons for last two months:

        sii_shp --monthly --polygon --latest 2

    - Generate monthly median polylines for a range of months between June
      and August

        sii_shp --monthly --median --polyline --date-range 2010-06-01,2010-08-01

    - Generate the polylines for a particular day: [unimplemented]

        sii_shp --daily --polyline -y 2012 -m 9 -d 16
        sii_shp --daily --polyline -y 2012 -doy 260

    """

    config = _process_cli_config(kwargs)

    shp_func_confs = []

    if config['median']:
        if config['daily'] and config['polyline'] and config['median']:
            config = copy.deepcopy(config)
            config = _conf_set_shape(config, 'polyline')
            configs = _confs_per_hemi(config)
            configs = _confs_per_period(configs, ['dayofyear'])

            shp_func_confs.extend(product([daily_median], configs))

        if config['monthly'] and config['polyline'] and config['median']:
            config = copy.deepcopy(config)
            config = _conf_set_shape(config, 'polyline')
            configs = _confs_per_hemi(config)
            configs = _confs_per_period(configs, ['month'])

            shp_func_confs.extend(product([monthly_median_polyline], configs))

    else:
        if config['monthly'] and config['polygon']:
            config = copy.deepcopy(config)
            config = _conf_set_shape(config, 'polygon')
            configs = _confs_per_hemi(config)
            configs = _confs_per_period(configs, ['year', 'month'])

            shp_func_confs.extend(product([monthly_polygon], configs))

        if config['monthly'] and config['polyline']:
            config = copy.deepcopy(config)
            config = _conf_set_shape(config, 'polyline')
            configs = _confs_per_hemi(config)
            configs = _confs_per_period(configs, ['year', 'month'])

            shp_func_confs.extend(product([monthly_polyline], configs))

    count = len(shp_func_confs)

    if count == 0:
        raise SeaIceShapefilesError('Config results in 0 shapefiles to create')

    log.info('Creating {count} shapefiles...'.format(count=count))

    p = Pool()

    exceptions = p.map(func_exec, shp_func_confs)
    exceptions = '\n'.join([e for e in exceptions if e is not None])
    if len(exceptions) > 0:
        raise SeaIceShapefilesError('Encountered exceptions while generating '
                                    'shapefiles: {}'.format(exceptions))


def func_exec(argstuple):
    """Execute a shapefile-generating function with given config. This function can
    be used with multiprocessing.Pool.map to execute many different functions at
    once; Pool.map passes only a single argument to the function it is given, so
    a wrapper like this is needed to execute different functions in one pool.

    Returns None on successful execution, otherwise returns the exception raised.

    Arguments:
    ----------
    argstuple: tuple of arguments. (function, config)

    """
    tb = None
    func, conf = argstuple

    try:
        func(conf)
    except SeaIceDataNoData as e:
        _alert_no_data(conf)
    except Exception as e:
        log.exception('Exception caught in {} with conf {}'.format(__name__, conf))
        tb = traceback.format_exc()
    return tb


def _alert_no_data(conf):
    date_desc_list = []

    if 'year' in conf:
        date_desc_list.append('year: {}'.format(conf['year']))

    if 'month' in conf:
        date_desc_list.append('month: {}'.format(conf['month']))

    if 'day' in conf:
        date_desc_list.append('day: {}'.format(conf['day']))

    if 'dayofyear' in conf:
        date_desc_list.append('dayofyear: {}'.format(conf['dayofyear']))

    if 'range' in conf:
        date_desc_list.append('year_range: {}'.format(conf['range']))

    date_desc = ', '.join(date_desc_list)

    log.warning('No Data found for hemi: {hemi}, {date_desc}; skipping....'.format(
        hemi=conf['hemi']['short_name'], date_desc=date_desc))


def _conf_set_shape(config, kind):
    """Return a copy of config, updating its polygon and polyline values such that
    polygon xor polyline is true.

    """
    conf = copy.deepcopy(config)

    other = {
        'polygon': 'polyline',
        'polyline': 'polygon'
    }[kind]

    conf.update({
        kind: True,
        other: False
    })

    return conf


def _confs_per_hemi(config):
    """Return a list of configs; one config per hemi found in the given config's
    'hemis' key. The new configs have an additional 'hemi' property.

    """
    confs = []

    for hemi in config['hemis']:
        c = copy.deepcopy(config)
        c['hemi'] = hemi
        confs.append(c)

    return confs


def _confs_per_period(configs, keys):
    """Return a list of configs; each config in the given list is copied into one
    config per date in its date_index, and these configs have additional
    properties taken from that date_index based on the given keys.

    For exapmle, if a list of just one config is passed in, and its date_index
    has two periods in it, Jan 2007 and Feb 2007, then
    _confs_per_period(configs, ['year', 'month']) returns a list of 2 configs;
    in addition to the properties they initially had, the first has {'year':
    2007, 'month': 1} and the second has {'year': 2007, month: 2}.

    """
    confs = []

    for conf in configs:
        for date in conf['date_index']:
            c = copy.deepcopy(conf)
            for key in keys:
                c[key] = getattr(date, key)
            confs.append(c)

    return confs


def _set_defaults_temporal(config_in):
    """Return modified config when no temporal args are provided.

    If 'median' is true use "--all" otherwise set "--latest=1"

    """
    config = copy.deepcopy(config_in)
    temporal_args = ('dayofyear', 'month', 'day',
                     'year', 'latest', 'date_range')
    if not config['all']:
        has_temporal_args = any((arg in config) for arg in temporal_args)
        if not has_temporal_args:
            if config['median']:
                config['all'] = True
            else:
                config['latest'] = 1

    return config


def _process_cli_config(cli_config):
    """Merge the command line configuration with the defaults, and infer other
    useful settings to add to the config dictionary.

    Arguments
    ---------
    cli_config: dictionary containing the command line arguments as parsed by
        click.

    """
    config = copy.deepcopy(DEFAULTS)

    config.update(_config_from_cli(cli_config))

    hemis = copy.deepcopy(config['hemi'])

    config['hemis'] = []

    if 'N' in hemis:
        config['hemis'].append(nt.NORTH)

    if 'S' in hemis:
        config['hemis'].append(nt.SOUTH)

    _validate_config(config)

    config = _set_defaults_temporal(config)

    config['date_index'] = _date_index(config)

    if config['debug_config']:
        pprint.pprint(config)
        exit(0)

    return config


def _date_index(config):
    """Returns a pandas.DatetimeIndex for the given config, based on the values of
    the options daily, monthly, year, month, day, dayofyear, latest, all, and
    median.

    For a median config, the base index is a single leap year; otherwise, the
    base index is a date index from the beginning of the satellite era to the
    present. Then the index is narrowed down based on the other temporal
    options.

    """

    if config['monthly']:
        freq = 'M'
    elif config['daily']:
        freq = 'D'

    # if monthly and daily aren't specified, we'll hit an error soon, but if
    # we're just wanting to debug parts of the config, then we don't care about
    # the date index and should return None here instead of erroring
    elif config['debug_config']:
        return None

    # when taking the median, we don't care about a particular year, but we
    # can't have a date index without years, so we should just look at one year
    # instead of the full satellite era, and it should be a leap year so that
    # Feb 29 and dayofyear 366 are valid inputs
    if config['median']:
        start = dt.date(2000, 1, 1)
        end = dt.date(2000, 12, 31)

    else:
        start = nt.BEGINNING_OF_SATELLITE_ERA
        end = pd.Timestamp.now() - pd.Timedelta('1 day')

    date_index = pd.date_range(start=start, end=end, freq=freq)

    if config['all']:
        return date_index

    if 'latest' in config:
        return date_index[-config['latest']:]

    if config.get('date_range'):
        start_date, end_date = config['date_range']

        # Set start date's day to the beginning of the month
        start_date = start_date.replace(day=1)

        # End date's day should be the end of the month:
        _, end_day = monthrange(end_date.year, end_date.month)
        end_date = end_date.replace(day=end_day)

        # Filter the date index by start/end_date
        date_index = date_index[(date_index.date >= start_date) &
                                (date_index.date <= end_date)]

        return date_index

    for attr in ('year', 'month', 'day', 'dayofyear'):
        if attr in config:
            date_index = date_index[getattr(date_index, attr) == config[attr]]

    return date_index


def _config_from_cli(cli_args):
    """Parse command line config settings into more useful types.

    """
    cli_config = dict((k, v) for k, v in cli_args.items() if v is not None)

    parse = {
        'search_paths': lambda x: [path for path in x.split(',')],
        'range': lambda x: [int(year) for year in x.split(',')],
        'hemi': lambda x: [h for h in x.split(',')]
    }

    for key, parser in parse.items():
        if key in cli_config:
            cli_config[key] = parser(cli_config[key])

    return cli_config


def _validate_config(config):
    """Raise an error if the config contains settings which are incorrect or
    internally inconsistent.

    """
    errors = []

    def error(msg):
        errors.append('Invalid configuration: {}'.format(msg))

    if ('year' in config) and ('month' in config):
        if TODAY < dt.date(config['year'], config['month'], 1):
            error('Cannot create shapefile for the future.')

    if config['median'] and config['polygon']:
        error('Median polygons are not supported. Use --polyline.')

    if not (config['daily'] ^ config['monthly']):
        error('Exactly one of --daily or --monthly must be chosen.')

    if not (config['polygon'] ^ config['polyline']):
        error('Exactly one of --polygon or --polyline must be chosen.')

    if config['monthly'] and ('dayofyear' in config):
        error('Cannot specify a day of year for a monthly shapefile.')

    if config['monthly'] and ('day' in config):
        error('Cannot specify a day for a monthly shapefile.')

    if config['median'] and ('year' in config):
        error('Cannot specify a year for a climatology median shapefile.')

    if config['median'] and ('latest' in config):
        error('Cannot specify latest for a climatology median shapefile.')

    if config['median'] and config['daily']:
        if 'month' in config or 'day' in config:
            error('Cannot specify "month" or "day" for a daily climatology median '
                  'shapefile. Use "dayofyear".')

    if config['daily'] and config.get('date_range'):
        error('Date ranges for daily shapefiles are not supported.')

    if config['median'] and config.get('date_range'):
        error('Date ranges for median shapefiles are not supported')

    is_used = set(arg for arg in ('dayofyear', 'month', 'day', 'year', 'latest', 'date_range')
                  if arg in config)

    # since 'all' is a flag, click always includes it; we care whether it's True
    # or not, not whether it is present in the config dict or not
    if config['all']:
        is_used.add('all')

    # args from different lists here cannot be used, i.e., 'latest' is
    # incompatible with 'month'
    temporal_arg_lists = [['all'], ['latest'], ['dayofyear', 'year'],
                          ['month', 'day', 'year'], ['date_range']]

    used_args_are_valid_subset = any(is_used.issubset(arg_list) for arg_list in temporal_arg_lists)

    if not used_args_are_valid_subset:
        error(('Found {}; can only create shapefiles for one of: all, latest, year/dayofyear, '
              'year/month/day').format(is_used))

    if errors:
        error_str = '\n'.join(errors)
        if config['debug_config']:
            config['errors'] = error_str
        else:
            log.error(error_str)
            raise SeaIceShapefilesError(error_str)


if __name__ == '__main__':
    cli()
