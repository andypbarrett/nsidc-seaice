import copy

import click
import pandas as pd

from .. import sedna
from seaice import version_flag
from .util import DAILY_STATISTICS_DEFAULT_CONFIG
from .util import load_config
from .util import options
import seaice.nasateam as nt
import seaice.logging as sil

log = sil.init('seaice.sedna')


@click.command()
@version_flag
@options(['daily', 'base', 'regression'])
@click.option('-i', '--interpolation_radius',
              type=int,
              default=None,
              help=('If non-zero, search this many days before and after the target date for files'
                    'to use to interpolate any missing data in the target file. Defaults to 1 as '
                    'this endpoint is primarily used for updating near-real-time data; using 0 '
                    'is preferred for final data.'))
@sil.log_command(log)
def update_sea_ice_statistics_daily(hemisphere, configfile, start_date, end_date,
                                    interpolation_radius, eval_days, regression_delta_km2):
    """Update the data values in the data store for a given date and/or range of
    dates. If none are specified, the previous five days are used. The
    configfile is a YAML file that overrides the defaults for the following
    options:

    \b
        extent_threshold: the cutoff percentage value for extents (default: 15.0)

    \b
        interpolation_radius: the number of days before and after a date that
            should be used to fill in any missing values (default: 1)

    \b
        search_paths: a list of paths to nasateam sea ice concentration data
            (default:
            ['/projects/DATASETS/nsidc0051_gsfc_nasateam_seaice/final-gsfc',
            '/projects/DATASETS/nsidc0081_nrt_nasateam_seaice'])

    \b
        pole_hole_value: the value found in the data files representing the pole
            hole (default: 251)

    \b
        data_store: name of the file to update/create (default: ./daily.csv)

    \b
        regional_masks: a list of regional masks for which statistics should be
            generated. By default, Meier's 2007 Arctic masks are used
            (nasateam.DEFAULT_NORTH_REGIONAL_MASKS). Example YAML configuration:

                regional_masks:
                  - name: 'meier2007'
                    file: 'path/to/binary/mask/regional_mask.msk'
                    hemisphere: north
                    regions:
                      hudson: 4
                      stlawrence: 5

            The specified file must contain a binary file with values in uint8
            format. The mask file can contain any number of region values; only
            those listed under 'regions' will be used. With this example, the
            output file would have columns "meier2007_hudson_extent_km2",
            "meier2007_hudson_area_km2", etc.

    """
    _update_sea_ice_statistics_daily(hemisphere, configfile, start_date, end_date,
                                     interpolation_radius, eval_days, regression_delta_km2)


def _update_sea_ice_statistics_daily(hemisphere=None, configfile=None, start_date=None,
                                     end_date=None, interpolation_radius=None,
                                     eval_days=None, regression_delta_km2=None):

    dates = pd.period_range(start_date, end_date)
    config = copy.deepcopy(DAILY_STATISTICS_DEFAULT_CONFIG)
    config.update(load_config(configfile))
    config['hemisphere'] = nt.by_name(hemisphere)
    config['grid_areas'] = config['hemisphere']['grid_areas']
    config['update_date_list'] = True
    config['regression_delta_km2'] = regression_delta_km2
    config['eval_days'] = eval_days
    if interpolation_radius is not None:
        config['interpolation_radius'] = interpolation_radius

    update_without_errors = sedna.update_sea_ice_statistics_daily(dates=dates, config=config)
    if not update_without_errors:
        log.warn('Update_sea_ice_statistics_daily returned with validation failures')
        exit(1)
    log.info('Update_sea_ice_statistics_daily complete')


if __name__ == '__main__':
    update_sea_ice_statistics_daily()
