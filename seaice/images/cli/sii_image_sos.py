import datetime as dt
import os

import click
import numpy as np
import pandas as pd

from .. import api
from seaice import version_flag
import seaice.nasateam as nt
import seaice.logging as seaicelogging


log = seaicelogging.init('seaice.images')


class DateType(click.ParamType):
    name = 'date'

    def convert(self, value, param, ctx):
        try:
            return dt.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            self.fail('%s is not a valid %%Y-%%m-%%d date' % value, param, ctx)


@click.command()
@version_flag
# required parameters
@click.option('-d', '--days-per-image', type=int, required=True, default=10,
              help=('Number of days to average for each image. Defaults to 10.'))
@click.option('-s', '--start-date', type=DateType(),
              help=('Start date (YYYY-MM-DD). Required unless --all is used.'))
@click.option('-e', '--end-date', type=DateType(),
              help=('End date (YYYY-MM-DD). If the time period from --start-date to --end-date '
                    'cannot be evenly partitioned according to --days-per-image, then a later '
                    'end date will be calculated and used. Required unless --all is used.'))
@click.option('--all', is_flag=True, default=False,
              help='Creates images for all dates since {}. Overrides --start-date '
              'and --end-date. Compatible with -m to create an image of the given month'
              ' for all years.'.format(nt.BEGINNING_OF_SATELLITE_ERA.strftime('%Y-%m-%d')))
# optional parameters
@click.option('-o', '--output', default=os.path.join(nt.SEA_ICE_BASE_DIR, 'sos'),
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
              help='Output directory.')
@click.option('-c', '--config_filename', default=None,
              help='Alternative configuration yaml file.  Must have all necessary options.')
@click.option('--allow-bad-data', is_flag=True, default=False,
              help='Ignore any errors in source data and create an image')
@click.option('-m', '--month', type=int, help=('MM. Month. Compatible with --all to create'
                                               ' an sos image for all years of the given month'))
@click.option('--overwrite/--no-overwrite', default=True,
              help='Overwrite existing images. --no-overwrite can be used to '
              'skip image generation if the target output image is already '
              'found to save time.')
@seaicelogging.log_command(log)
def sii_image_sos(**config):
    datetime_indexes = _datetime_indexes(config['start_date'],
                                         config['end_date'],
                                         config['days_per_image'],
                                         config['all'],
                                         config['month'])

    count = len(datetime_indexes)
    log.info('Creating {count} image{s}...'.format(count=count,
                                                   s='' if count == 1 else 's'))

    for datetime_index in datetime_indexes:
        api.sos_image(datetime_index,
                      output=config['output'],
                      config_filename=config['config_filename'],
                      allow_bad_data=config['allow_bad_data'],
                      overwrite=config['overwrite'])


def _datetime_indexes(start_date, end_date, days_per_image, all_dates, month):
    if all_dates:
        start_date = nt.BEGINNING_OF_SATELLITE_ERA
        end_date = dt.date.today() - dt.timedelta(days=1)

    if (start_date is None) or (end_date is None):
        raise ValueError('either --all or both --start-date and --end-date must be given.')

    days = pd.date_range(start_date, end_date)
    if month:
        days = days[days.month == month]

    datetime_indexes = []
    for year, date_range in sorted(days.groupby(days.year).items()):
        # add extra days until we can divide the range evenly into pieces that are
        # each `days_per_image` long
        while len(date_range) % days_per_image != 0:
            next_day = date_range[-1] + dt.timedelta(days=1)
            date_range = date_range.append(pd.DatetimeIndex([next_day]))

        datetime_indexes.extend(np.split(date_range, len(date_range) / days_per_image))

    return datetime_indexes


if __name__ == '__main__':
    sii_image_sos()
