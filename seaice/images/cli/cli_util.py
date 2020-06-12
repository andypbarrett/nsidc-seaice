"""functions used by multiple seaiceimages CLI modules"""

import datetime as dt
import os

import click
import pandas as pd

from ..errors import SeaIceImagesBadCommandLineArguments
import seaice.nasateam as nt


class DateRangeType(click.ParamType):
    name = 'DateRange'

    def __init__(self, date_fmt='%Y%m%d'):
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


def get_dates(config):
    """Returns a list of dates to create images for, based on
    config passed via click's commandline options.
    """
    if config.get('year') and not config.get('all'):
        # The user pased a particular date via -y -m -d options
        return [dt.date(config['year'], config['month'], config['day'])]

    temporality = config['temporality']

    # The 'range' and 'all' options generate a range of dates using
    # pd.period_range. Set the frequency here.
    frequency = {'daily': 'D', 'monthly': 'M'}[temporality]

    if config.get('latest'):
        return _get_latest_n_dates(frequency, config['latest'])

    if config['range']:
        start_date, end_date = config['range']
        latest_valid_date = _get_latest_date(frequency)[0]
        end_date = min(end_date, latest_valid_date)
        return _get_date_range(start_date, end_date, frequency)

    elif config['all']:
        start_date = {
            'D': nt.BEGINNING_OF_SATELLITE_ERA,
            'M': nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY
        }[frequency]
        end_date = _get_latest_date(frequency)[0]
        date_range = pd.period_range(start=start_date, end=end_date, freq=frequency)

        for key in ('year', 'month', 'day'):
            if config.get(key):
                date_range = date_range[getattr(date_range, key) == config[key]]

        return date_range.to_timestamp().date


def validate_command_line_options(opts):
    """ Check that required input parameters were provided on the command line """

    def ensure_argument(arg):
        """ Ensure argument in config is not 'None'. """
        if not opts[arg]:
            raise(SeaIceImagesBadCommandLineArguments(
                'command line must provide a {} for a {} image.'.format(
                    arg, opts['temporality'])))

    required_args = []
    if not opts.get('google', False):
        required_args.append('hemi')

    if not opts.get('latest') and not opts.get('all') and not opts.get('range'):
        required_args.extend(['year', 'month'])

        if opts['temporality'] is 'daily':
            required_args.append('day')

        elif opts['temporality'] is 'monthly' and not opts.get('day'):
            opts['day'] = 1
    else:
        # Single-date keys are not compatible.
        # with --latest and --range.
        conflicting_args = []
        if not opts.get('all'):
            for key in ('day', 'month', 'year'):
                if opts.get(key):
                    conflicting_args.append(key)

        # Ensure there are not conflicting latest/all/range args.
        selected = None
        for key in ('latest', 'range', 'all'):
            if opts.get(key):
                if not selected:
                    selected = key
                else:
                    conflicting_args.append(key)

        # Raise an error if there are conflicting args.
        # We want to make sure that the user is aware of their mistake.
        if conflicting_args:
            raise(SeaIceImagesBadCommandLineArguments(
                'The following arguments are not compatible '
                'with --{}: {}'.format(selected, conflicting_args)))

    if opts.get('image_type') is 'anomaly':
        required_args.append('year_range')

    for arg in required_args:
        ensure_argument(arg)

    if opts.get('output') and (not os.path.isdir(opts['output'])):
        bad_output = False
        for key in ('range', 'all'):
            if opts.get(key):
                bad_output = True

        if ',' in opts.get('hemi', ''):
            bad_output = True

        if opts.get('latest') and (opts.get('latest') > 1):
            bad_output = True

        if bad_output:
            raise(SeaIceImagesBadCommandLineArguments(
                'When using options that create multiple output files, the '
                'value of --output must be an existing directory.'))

    # Raise an error if a user requests a blue marble version of an incompatible
    # image_type.
    if opts.get('blue_marble') and opts.get('image_type') not in ('extent', 'concentration'):
        raise(SeaIceImagesBadCommandLineArguments(
            'The --blue_marble option is not compatible with the'
            ' {} image type'.format(opts.get('image_type'))))

    # Raise an error if the user requests a non-trend image with the
    # --trend_start_year opt
    if opts.get('trend_start_year') and opts.get('image_type') != 'trend':
        raise(SeaIceImagesBadCommandLineArguments(
            'The --trend_start_year option is not compatible with the'
            ' {} image type'.format(opts.get('image_type'))))

    opts['values'] = {}
    for value in opts.pop('value', ()):
        k, v = value.split('=')
        opts['values'][k] = v

    return opts


def _get_date_range(start_date, end_date, frequency):
    dates = pd.period_range(start=start_date, end=end_date, freq=frequency)
    return [dt.date(year=date.year, month=date.month, day=date.day) for date in dates]


def _get_latest_date(freq):
    return _get_latest_n_dates(freq, 1)


def _get_latest_n_dates(freq, periods):
    periods = periods + 1
    end = dt.date.today()

    dates = pd.period_range(periods=periods, end=end, freq=freq).to_timestamp().date
    dates = dates[:-1]
    dates = list(dates)

    return dates
