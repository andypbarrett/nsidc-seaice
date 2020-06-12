import copy
import datetime as dt
import fnmatch
import os
import shutil

import click
import pandas as pd

from .. import sedna
from seaice import version_flag
from ..errors import SednaError
from .util import DAILY_STATISTICS_DEFAULT_CONFIG
from .util import archive_existing_datastore
import seaice.logging as sil
import seaice.nasateam as nt


log = sil.init('seaice.sedna')


@click.command()
@version_flag
@sil.log_command(log)
def initialize_sea_ice_statistics_daily():
    """Use all of the default configurations to generate all of the standard daily
    sea ice statistics for each hemisphere. The default search paths
    ('/projects/DATASETS/nsidc0051_gsfc_nasateam_seaice/final-gsfc' and
    '/projects/DATASETS/nsidc0081_nrt_nasateam_seaice') must be mounted. Final
    data is not interpolated, while near-real-time data is interpolated with an
    interpolation radius of 1. A new datastore is created and any pre-existing
    datastore is renamed with a current timestamp.

    """
    _initialize_sea_ice_statistics_daily()


def _initialize_sea_ice_statistics_daily():
    data_store = DAILY_STATISTICS_DEFAULT_CONFIG['data_store']

    temp_data_store = data_store.replace('.p', '_building.p')
    if os.path.exists(temp_data_store):
        os.remove(temp_data_store)

    archive_existing_datastore(data_store)
    _initialize_sea_ice_statistics_daily_by_hemisphere('N', temp_data_store)
    log.info('Northern hemisphere initialized for {}'.format(temp_data_store))
    _initialize_sea_ice_statistics_daily_by_hemisphere('S', temp_data_store)
    log.info('Sourthern hemisphere initialized for {}'.format(temp_data_store))
    shutil.move(temp_data_store, data_store)
    log.info('Data store {} updated with newly initialized values'.format(data_store))


def _initialize_sea_ice_statistics_daily_by_hemisphere(hemisphere, temp_data_store):
    """Generate all of the standard daily statistics for the desired hemisphere. By
    default, final data and near-real-time require a different interpolation radius.

    """
    config = copy.deepcopy(DAILY_STATISTICS_DEFAULT_CONFIG)
    config['hemisphere'] = nt.by_name(hemisphere)
    config['grid_areas'] = config['hemisphere']['grid_areas']
    config['update_date_list'] = True
    config['data_store'] = temp_data_store

    final_date_cutoff = _get_last_date_with_finalized_data()

    final_dates = pd.period_range(nt.BEGINNING_OF_SATELLITE_ERA, final_date_cutoff)
    final_config = copy.deepcopy(config)
    final_config['interpolation_radius'] = 0
    sedna.update_sea_ice_statistics_daily(dates=final_dates, config=final_config,
                                          validate_data=False)

    first_nrt_date = final_date_cutoff + dt.timedelta(1)
    yesterday = dt.date.today() - dt.timedelta(1)
    nrt_dates = pd.period_range(first_nrt_date, yesterday)
    sedna.update_sea_ice_statistics_daily(dates=nrt_dates, config=config)


def _get_last_date_with_finalized_data():
    """Use files found in the default search paths to figure out the last date which
    has final data.

    """

    ice_files = []

    assert type(nt.DEFAULT_FINAL_SEA_ICE_PATHS) == list
    for directory in nt.DEFAULT_FINAL_SEA_ICE_PATHS:
        log.info('Searching for sea ice files in: {}'.format(directory))
        for root, dirs, files in os.walk(directory):
            ice_files.extend([os.path.join(root, f) for f in fnmatch.filter(files, '*nt_*.bin')])

    matches = [nt.DATA_FILENAME_MATCHER.search(f) for f in ice_files]

    all_final_dates = [m.group('date') for m in matches if m.group('day')]
    all_final_dates = [dt.datetime.strptime(d, '%Y%m%d').date() for d in all_final_dates]
    all_final_dates = [d for d in all_final_dates if d <= nt.LAST_DAY_WITH_VALID_FINAL_DATA]

    if len(all_final_dates) is 0:
        raise SednaError('No final daily data found on default search path.')

    date = max(all_final_dates)

    log.info('Found date {} for last date with final daily data.'.format(date))

    return date


if __name__ == '__main__':
    initialize_sea_ice_statistics_daily()
