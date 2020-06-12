from calendar import monthrange
import copy
import logging

import numpy as np
import pandas as pd

from . import cube
from . import errors as e
from . import getter
from . import grid_filters
import seaice.nasateam as nt
import seaice.datastore as sds


log = logging.getLogger(__name__)


def apply_filters(gridset_in, filters):
    gridset = copy.deepcopy(gridset_in)

    gridset_repr = '<gridset at {}>'.format(hex(id(gridset)))
    log.debug('Copied gridset {0} to {1}'.format(gridset_in, gridset_repr))

    for filter_ in filters:
        log.debug('Applying filter {0} to {1}'.format(filter_, gridset_repr))
        gridset = filter_(gridset)

    return gridset


def apply_largest_pole_hole(gridset_in):
    gridset = copy.deepcopy(gridset_in)

    pole_hole = gridset['metadata']['flags']['pole']

    try:
        largest_pole_hole = np.any(gridset['data'] == pole_hole, axis=2)
    except ValueError:  # 'axis' entry is out of bounds; we don't have 3D data
        return gridset

    for i in np.arange(gridset['data'].shape[2]):
        if np.all(gridset['data'][:, :, i] == gridset['metadata']['missing_value']):
            continue
        gridset['data'][largest_pole_hole, i] = pole_hole

    return gridset


def concentration_cutoff(cutoff, gridset_in):
    gridset = copy.deepcopy(gridset_in)

    gridset['data'] = grid_filters.concentration_cutoff(cutoff, gridset['data'])

    return gridset


def concentration_to_extent(extent_threshold, gridset_in):
    gridset = copy.deepcopy(gridset_in)
    conc = gridset['data']

    max_valid = gridset['metadata']['valid_data_range'][1]

    gridset['data'] = _extent_grid_from_conc_grid(
        conc,
        flags=gridset['metadata']['flags'],
        missing_value=gridset['metadata']['missing_value'],
        valid_extent_range=(extent_threshold, max_valid)
    )

    gridset['metadata']['valid_data_range'] = (0, 1)

    return gridset


def ensure_full_nrt_month(gridset):
    """Ensure that monthly gridsets generated with daily (NRT) data contain data
    for all days of that month, if not raise Exception"""
    metadata = gridset['metadata']

    if (metadata['temporality'] != 'M'):
        log.warn('Attempted to verify full filelist for a nrt '
                 'month on a non-monthly gridset with '
                 'metadata: {}'.format(metadata))
        return gridset

    # Only filter if there is a daily period_index
    # If using a monthly period index, this isn't NRT *or* is empty due to
    # too few daily files to allow a valid monthly file.
    if metadata['period_index'].freqstr == 'D':
        period = gridset['metadata']['period']
        if monthrange(period.year, period.month)[1] != len(gridset['metadata']['files']):
            raise e.IncompleteNRTGridsetError

    return gridset


def drop_bad_dates(gridset_in):
    gridset = copy.deepcopy(gridset_in)

    if gridset['metadata']['temporality'] == 'M':
        log.warn('Tried to drop bad dates from a monthly gridset, '
                 'with metadata: {}'.format(gridset['metadata']))
        return gridset

    sds_bad_days = sds.get_bad_days_for_hemisphere(gridset['metadata']['hemi'])
    bad_period_index = pd.PeriodIndex(sds_bad_days, freq='D')
    bad_period_index = gridset['metadata']['period_index'].intersection(bad_period_index)

    if len(bad_period_index) == 0:
        log.debug('No bad dates found, returning input gridset')
        return gridset

    good_dates = gridset['metadata']['period_index'].difference(bad_period_index)

    if len(good_dates) == 0:
        freq = gridset['metadata']['temporality']

        log.debug('drop_bad_dates: No good dates found, returning empty gridset.')
        shape = gridset['data'].shape[0:2]
        period = gridset['metadata']['period']
        temporality = gridset['metadata']['temporality']
        gridset = getter.empty_gridset(shape, temporality, period=period)

        gridset['metadata']['files'] = []
        gridset['metadata']['period_index'] = pd.PeriodIndex([], freq=freq)

        return gridset

    files = []
    indices = []
    for date in good_dates:
        # pd.Index.get_loc doesn't handle the same date being at multiple
        # locations (double-weighted SMMR) well, so we can use np.where instead
        [date_indices] = np.where(gridset['metadata']['period_index'] == date)
        for index in date_indices:
            indices.append(index)
            files.append(gridset['metadata']['files'][index])

    gridset['data'] = gridset['data'][:, :, indices]
    gridset['data'] = np.ma.squeeze(gridset['data'])

    gridset['metadata']['files'] = files

    # if gridset['metadata']['period_index'] has any of the same date twice
    # (double-weighted SMMR), good_dates will have those dates only once; taking
    # the intersection will get the right number
    gridset['metadata']['period_index'] = gridset['metadata']['period_index'].intersection(
        good_dates
    )

    return gridset


def drop_invalid_ice(invalid_ice_mask, gridset_in):
    """Apply the given invalid ice mask to the gridset.

    Remove ice and missing values from areas of open water (ice not possible)
    and set them to 0.

    """
    gridset = copy.deepcopy(gridset_in)

    if np.all(gridset['data'] == gridset['metadata']['missing_value']):
        return gridset

    if invalid_ice_mask.shape != gridset['data'].shape:
        layers = gridset['data'].shape[2]
        invalid_ice_mask = np.dstack([invalid_ice_mask] * layers)

        for layer in np.arange(layers):
            if np.all(gridset['data'][:, :, layer] == gridset['metadata']['missing_value']):
                invalid_ice_mask[:, :, layer] = False

    flagged = np.ma.masked_outside(gridset['data'], *gridset['metadata']['valid_data_range'])
    missing = np.ma.masked_equal(gridset['data'], gridset['metadata']['missing_value'])
    not_flagged = ~flagged.mask | missing.mask
    invalid_ice_or_ocean = invalid_ice_mask & not_flagged

    gridset['data'] = np.where(invalid_ice_or_ocean, 0, gridset['data'])
    gridset['metadata']['drop_invalid_ice'] = True

    return gridset


def drop_land(land, coast, gridset_in):
    gridset = copy.deepcopy(gridset_in)

    ice_only = gridset['data']
    for type_ in [land, coast]:
        ice_only[ice_only == type_] = 0

    gridset['data'] = ice_only
    gridset['metadata']['drop_land'] = True

    return gridset


def interpolate(gridset_in):
    """Interpolate surrounding days into target date's data for missing days

       Given a gridset of data, a target date to interpolate, and a period index
       that defines the dates of each element in the gridset data array;
       update the gridset such that missing values in the gridset for the
       target date are interpolated from the other days' data"""

    gridset = copy.deepcopy(gridset_in)
    date = gridset['metadata']['period']
    period_index = gridset['metadata']['period_index']
    file_list = gridset['metadata']['files']
    data = gridset['data']

    if len(period_index) == 1:
        return gridset

    shape = data.shape[0:2]

    if date in period_index:
        try:
            index = _index_by_date(file_list, date)

            interpolation_grids = np.delete(data, index, axis=2)
            original_grid = data[:, :, index].copy()

            gridset['data'] = _interpolate_missing(original_grid, interpolation_grids)

            if np.all(gridset['data'] == original_grid):
                file_for_this_date = file_list[index]
                gridset['metadata']['files'] = [file_for_this_date]
            return gridset

        except e.IndexNotFoundError:
            log.error('Data missing for valid target date when attempting to interpolate'
                      ' {} on {}, data will be interpolated from '
                      'surrounding data only.'.format(date, period_index))

    interpolation_grids = data
    empty_grid = np.full(shape, nt.FLAGS['missing'], dtype=np.int)
    gridset['data'] = _interpolate_missing(empty_grid, interpolation_grids)

    return gridset


def prevent_empty(gridset):
    all_missing = np.all(gridset['data'] == gridset['metadata']['missing_value'])

    no_data = 0 in gridset['data'].shape

    was_empty = gridset['metadata'].get('empty_gridset', False)

    if all_missing or no_data or was_empty:
        raise e.SeaIceDataNoData()

    return gridset


def _extent_grid_from_conc_grid(conc,
                                flags={},
                                missing_value=None,
                                valid_extent_range=(nt.EXTENT_THRESHOLD, 100)):
    """Take a grid of concentration values and return an extent grid. Given flag
    values will be preserved in the return grid, except that gridcells flagged
    as pole values will be counted as part of the extent. Extent gridcells are
    marked as 1, flag values are preserved, and all other gridcells are 0.

    Arguments:
    ----------
    conc: numpy 2d-array (float) of concentration values

    flags: dict (string -> int) of special flag values (ie not a concentration
        percentage). If flags contains a 'pole' key, that value will be counted
        as part of the extent. Defaults to empty dict.

    valid_extent_range: tuple, the minimum and maximum concentration values to
        count as part of the extent

    """
    flags = copy.deepcopy(flags)
    if missing_value:
        flags['missing'] = missing_value

    ice = ~np.ma.masked_outside(conc, *valid_extent_range).mask

    pole_hole_value = flags.pop('pole', None)
    if pole_hole_value:
        pole_hole = conc == pole_hole_value
    else:
        pole_hole = np.zeros_like(conc).astype('bool')

    extent_grid = (ice | pole_hole).astype('int')

    flag_grid = np.zeros_like(extent_grid)
    for flag in flags.values():
        flag_grid[conc == flag] = flag

    return (extent_grid + flag_grid)


def _index_by_date(filelist, date):
    """Return the index of the file that matches the desired year/month/day
    or raise IndexNotFoundError() if there are not matches"""

    yyyymmdd = date.strftime('%Y%m%d')

    dates = [nt.DATA_FILENAME_MATCHER.search(f).group('date') for f in filelist]

    try:
        idx = dates.index(yyyymmdd)
    except ValueError:
        raise e.IndexNotFoundError()

    return idx


def _interpolate_missing(target_grid,
                         interpolation_grids,
                         missing_value=nt.FLAGS['missing'],
                         valid_data_range=nt.VALID_DATA_RANGE):
    """Replace any occurences of missing_value in target_grid with the mean of
    interpolation_grids. Flag values outside of the valid_data_range are
    preserved.

    target_grid: np.ndarray with 2 dimensions

    interpolation_grids: np.ndarray with 3 dimensions; should be a "stack" of
        grids with the same shape as target_grid, ie,
        interpolation_grids.shape[0:2] == target_grid.shape

    missing_value: the value to replace on target_grid

    valid_data_range: values that should be considered data, and therefore
        preserved on target_grid; values outside this range that are not the
        missing_value are also preserved

    """
    no_interpolation_grids = (interpolation_grids.ndim < 3) or (interpolation_grids.shape[2] == 0)
    if no_interpolation_grids:
        return target_grid

    # mask everything outside of the valid range
    def masked(arr):
        return np.ma.masked_outside(arr, *valid_data_range)

    # mask everything in the valid range and missing; flag values are the only
    # thing not masked
    def flags(arr):
        flags_arr = np.ma.array(arr, mask=~masked(arr).mask)
        flags_arr = np.ma.masked_equal(flags_arr, missing_value)
        return flags_arr

    average = cube.average_cube(masked(interpolation_grids))

    if np.all(target_grid == missing_value):
        flag_layer = getter.flag_layer_from_cube(flags(interpolation_grids))
    else:
        flag_layer = flags(target_grid)

    interpolated_grid = cube.apply_patch(masked(target_grid), average)

    interpolated_grid = cube.apply_patch(interpolated_grid, flag_layer)

    interpolated_grid = interpolated_grid.filled(fill_value=missing_value)

    return interpolated_grid
