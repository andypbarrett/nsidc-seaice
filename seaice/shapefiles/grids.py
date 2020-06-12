import numpy as np

import seaice.data as sid
from .common import LAND, COAST


def grid(config, keep_flag_values=True, treat_coast_as_land=False):
    """Returns a numpy 2d array representing the ice to contour for the given
    config.

    config: config dict, as generated in the cli module

    keep_flag_values: if True, return a grid containing only 1s where there is
        ice extent and 0s everywhere else; if False, return the grid with flag
        values as returned by seaicedata

    """
    if config.get('daily', False) and config.get('median', False):
        start_year, end_year = config['range']

        gridset = sid.extent_daily_median(config['hemi'],
                                          start_year,
                                          end_year,
                                          dayofyear=config['dayofyear'],
                                          search_paths=config['search_paths'],
                                          extent_threshold=config['extent_threshold'],
                                          allow_empty_gridset=True,
                                          drop_invalid_ice=True,
                                          allow_bad_dates=False)

    elif config.get('monthly', False) and config.get('median', False):
        start_year, end_year = config['range']

        gridset = sid.extent_monthly_median(config['hemi'],
                                            start_year,
                                            end_year,
                                            config['month'],
                                            search_paths=config['search_paths'],
                                            extent_threshold=config['extent_threshold'],
                                            drop_invalid_ice=True,
                                            allow_empty_gridset=True)

    elif config.get('daily', False):
        gridset = sid.extent_daily(config['hemi'],
                                   config['year'],
                                   config['month'],
                                   config['day'],
                                   search_paths=config['search_paths'],
                                   extent_threshold=config['extent_threshold'],
                                   allow_empty_gridset=False,
                                   drop_invalid_ice=True,
                                   allow_bad_dates=False)

    elif config.get('monthly', False):
        gridset = sid.extent_monthly(config['hemi'],
                                     config['year'],
                                     config['month'],
                                     search_paths=config['search_paths'],
                                     extent_threshold=config['extent_threshold'],
                                     drop_invalid_ice=True,
                                     allow_empty_gridset=False)

    return _massage_grid(gridset['data'], keep_flag_values, treat_coast_as_land)


def _massage_grid(grid, keep_flag_values=True, treat_coast_as_land=False):
    if treat_coast_as_land:
        grid = _data_massage_land_like(grid, LAND, [COAST]).astype('int16')

    if not keep_flag_values:
        grid = (grid == 1).astype('int16')

    return grid.astype('int16')


def _data_massage_land_like(data, land_val=LAND, land_like_vals=[COAST]):
    """Convert land-like values to land.

    Returns a copy of the given data where any gridcells with a value in
    land_like_vals is replaced with land_val. For drawing monthly polylines, we
    treat land and coast as the same thing.

    Arguments:
    ----------
    data: numpy ndarray with sea ice extent values, as obtained from seaice.data

    land_val: the value that represents land in data

    land_like_vals: values that should be replaced with land, eg coast

    """

    land_like = np.in1d(data, land_like_vals).reshape(data.shape)

    return np.where(land_like, land_val, data)
