import copy
import os
import shutil

import click

from .. import sedna
from seaice import version_flag
from .util import DEFAULT_CONFIG_FILE
from .util import MONTHLY_STATISTICS_DEFAULT_CONFIG
from .util import archive_existing_datastore
from .util import load_config
import seaice.nasateam as nt
import seaice.logging as sil

log = sil.init('seaice.sedna')


@click.command()
@version_flag
@click.option('-c', '--configfile',
              type=str,
              default=DEFAULT_CONFIG_FILE,
              help='Path to YAML file containing config values.')
@sil.log_command(log)
def sea_ice_statistics_monthly(configfile):
    """Calculate monthly values by taking the monthly means of the daily values. The
    configfile is a YAML file that can override the defaults for the following
    options (if paths in the YAML file are relative, they are treated as
    relative to the YAML file):

    \b
        search_paths: a list of paths to nasateam sea ice concentration data
            (default: ['/projects/DATASETS/nsidc0051_gsfc_nasateam_seaice/final-gsfc',
                       '/projects/DATASETS/nsidc0081_nrt_nasateam_seaice'])

    \b
        data_store: name of the file to update/create (default: ./monthly.p)

    \b
        daily_data_store: name of the file used containing daily data (default:
        ./daily.p)

    """
    _sea_ice_statistics_monthly(configfile)


def _sea_ice_statistics_monthly(configfile):
    config = copy.deepcopy(MONTHLY_STATISTICS_DEFAULT_CONFIG)
    config.update(load_config(configfile))

    data_store = config.get('data_store', MONTHLY_STATISTICS_DEFAULT_CONFIG['data_store'])
    temp_data_store = data_store.replace('.p', '_building.p')
    if os.path.exists(temp_data_store):
        os.remove(temp_data_store)
    archive_existing_datastore(data_store)
    config['data_store'] = temp_data_store

    for hemi in ['N', 'S']:
        config['hemisphere'] = nt.by_name(hemi)
        config['grid_areas'] = config['hemisphere']['grid_areas']

        sedna.sea_ice_statistics_monthly(config)
        log.info('sea_ice_statistics_monthly complete')

    shutil.move(temp_data_store, data_store)
    log.info('renamed {} to {}'.format(temp_data_store, data_store))


if __name__ == '__main__':
    sea_ice_statistics_monthly()
