import calendar as cal
import datetime as dt
import getpass
import hashlib
import os
import socket
import sys

import click
import pandas as pd

from .. import api
from .. import grid_filters
from seaice import version_flag
from seaice import __version__ as VERSION
import seaice.nasateam as nt
import seaice.logging as sil

log = sil.init('seaice.data')

first_of_current_month = dt.date.today().replace(day=1)
last_day_of_previous_month = first_of_current_month - dt.timedelta(1)

DEFAULT_MONTH = '{:04}-{:02}'.format(last_day_of_previous_month.year,
                                     last_day_of_previous_month.month)


@click.command()
@click.option('-h', '--hemisphere',
              type=click.Choice(['N', 'S', 'both']), default='both',
              help=('Hemisphere for which to update the data. Can be "N", "S", '
                    'or "both" (default).'))
@click.option('-s', '--start-month', default=DEFAULT_MONTH,
              help='YYYY-MM. Default: {}.'.format(DEFAULT_MONTH))
@click.option('-e', '--end-month', default=DEFAULT_MONTH,
              help='YYYY-MM. Default: {}.'.format(DEFAULT_MONTH))
@click.option('-sp', '--search-paths', multiple=True,
              default=nt.DEFAULT_SEA_ICE_PATHS,
              help=('Paths to search for daily sea ice concentration files. '
                    'Default: {}').format(nt.DEFAULT_SEA_ICE_PATHS))
@click.option('--allow-empty-gridset/--no-allow-empty-gridset', default=True,
              help=('Allow the creation of "empty" binary files when a grid '
                    'could not be computed. Default: True.'))
@click.option('--drop-land/--no-drop-land', default=False,
              help=('Convert the land flag values ({}) to 0. '
                    'Default: False.'.format(nt.FLAGS['land'])))
@click.option('--drop-invalid-ice/--no-drop-invalid-ice', default=True,
              help=('Apply the 0622 mask to remove invalid ice (and set the '
                    'concentration value at that location to 0). '
                    'Default: True.'))
@click.option('--ensure-full-nrt-month/--no-ensure-full-nrt-month',
              default=False,
              help=('Require daily files to be present for every day in the '
                    'month; an error is thrown if any days are missing and '
                    'this value is True. Default: False.'))
@click.option('--min-days-for-valid-month', type=int,
              default=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
              help=('The number of days which must have data for a month to be '
                    'considered valid. An invalid month will not have a '
                    'monthly concentration grid generated for it. '
                    'Default: {}'.format(nt.MINIMUM_DAYS_FOR_VALID_MONTH)))
@click.option('--concentration-cutoff', default=nt.EXTENT_THRESHOLD, type=int,
              help=('Minimum ice concentration percentage to keep. '
                    'Concentration values below this cutoff are set to 0. '
                    'Default: {}.').format(nt.EXTENT_THRESHOLD))
@click.option('-o', '--output-dir', default=os.getcwd(),
              type=click.Path(exists=True, file_okay=False),
              help='Output directory (must already exist). If none is given, '
              'the current working directory is used. '
              'Default: {}'.format(os.getcwd()))
@version_flag
@sil.log_command(log)
def monthly_files_from_dailies(hemisphere, start_month, end_month,
                               search_paths,
                               allow_empty_gridset,
                               drop_land,
                               drop_invalid_ice,
                               ensure_full_nrt_month,
                               min_days_for_valid_month,
                               concentration_cutoff,
                               output_dir):
    """Create monthly concentration grids, computed by taking the mean of the daily
    grids."""

    timestamp = dt.datetime.now().isoformat()

    hemis = ['N', 'S'] if hemisphere == 'both' else [hemisphere]

    last_day_of_end_month = _last_day_of_yearmonth(end_month)
    dt_index = pd.date_range(start=start_month,
                             end='{}-{}'.format(end_month, last_day_of_end_month), freq='M')

    created_files = []

    for hemi in hemis:
        for yearmonth in dt_index:
            year = yearmonth.year
            month = yearmonth.month

            grid = _get_grid(
                hemisphere=nt.by_name(hemi),
                year=year,
                month=month,
                search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                allow_empty_gridset=allow_empty_gridset,
                drop_land=drop_land,
                drop_invalid_ice=drop_invalid_ice,
                ensure_full_nrt_month=ensure_full_nrt_month,
                min_days_for_valid_month=min_days_for_valid_month,
                concentration_cutoff=concentration_cutoff
            )

            # save the grid in a format usable by the scientists; "flat binary
            # gridded monthly field" (from an email from Julienne Stroeve dated
            # 2017-10-20, subject "[Rockhoppers] monthly near-real time data")
            filename = os.path.join(
                os.path.abspath(output_dir),
                'monthly-conc-grid-{hemi}-{year:04}-{month:02}.bin'.format(
                    hemi=hemi, year=year, month=month
                )
            )
            with open(filename, 'wb') as fid:
                grid.tofile(fid)
            print('wrote {}'.format(filename))
            created_files.append(filename)

    _write_metadata_file(timestamp, output_dir, created_files)


def _get_grid(hemisphere, year, month, search_paths,
              allow_empty_gridset,
              drop_land,
              drop_invalid_ice,
              ensure_full_nrt_month,
              min_days_for_valid_month,
              concentration_cutoff):
    """Returns just the grid (numpy.ndarray) of values for the monthly data matching
    the given criteria.

    seaicedata.api.concentration_monthly is called, then the concentration
    cutoff is applied for any values below the given threshold.

    """

    gridset = api.concentration_monthly(hemisphere, year, month, search_paths,
                                        allow_empty_gridset,
                                        drop_land,
                                        drop_invalid_ice,
                                        ensure_full_nrt_month,
                                        min_days_for_valid_month)

    grid = grid_filters.concentration_cutoff(concentration_cutoff, gridset['data'])

    return grid


def _last_day_of_yearmonth(yearmonth):
    """Returns the number of days (or, equivalently, the date of the last day) in
    the given yearmonth.

    yearmonth: (str) YYYY-MM

    """
    year, month = (int(val) for val in yearmonth.split('-'))
    last_day = cal.monthrange(year, month)[1]

    return last_day


def _md5sum(filename):
    """Returns the MD5 sum for the given file."""
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def _write_metadata_file(timestamp, output_dir, created_files):
    """Save a txt file with the seaicedata version and the command used to easily
    verify/recreate files in the future.

    """
    metadata_filename = os.path.join(
        os.path.abspath(output_dir),
        'monthly-conc-grid-metadata-{}.txt'.format(timestamp)
    )
    with open(metadata_filename, 'w') as f:
        f.write('{}\n'.format(timestamp))
        f.write('seaice v{}\n'.format(VERSION))

        f.write('\nuser: {}\n'.format(getpass.getuser()))
        f.write('host: {}\n'.format(socket.gethostname()))

        f.write('\nExecuted command: (according to Python\'s sys.argv)\n')
        f.write(str(sys.argv[:]))
        f.write('\n')

        f.write('\nCreated files: (FILENAME - MD5SUM)\n')
        for cf in created_files:
            f.write('{} - {}\n'.format(cf, _md5sum(cf)))

    print('wrote {}'.format(metadata_filename))


if __name__ == '__main__':
    monthly_files_from_dailies()
