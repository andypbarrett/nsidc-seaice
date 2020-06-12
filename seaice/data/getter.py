"""Functions for retrieving sea ice data from goddard formatted nasateam files.

"""
import calendar as cal
import copy
import datetime as dt
import functools
import logging
import re

import numpy as np
import pandas as pd

from . import cube
from . import errors as e
from . import gridset_filters as gf
from . import locator
import seaice.nasateam as nt

log = logging.getLogger(__name__)


def _validate_daily(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        date = kwargs.get('date', args[1])
        today = dt.date.today()

        if not (nt.BEGINNING_OF_SATELLITE_ERA <= date < today):
            raise e.DateOutOfRangeError()

        return func(*args, **kwargs)
    return func_wrapper


@_validate_daily
def concentration_daily(hemisphere, date, search_paths, interpolation_radius=0):
    """Return gridset containing daily sea ice concentration and metadata.
       Arguments:
       ----------
       hemisphere:           nasateam hemisphere to get data from (e.g. nt.NORTH)
       date:                 Date to acquire data for
       search_paths:         List of locations to search for data
       interpolation radius: Number of surrounding days to utilize when interpolating
                             source data to fill missing values
    """

    start_date = date - dt.timedelta(interpolation_radius)
    end_date = date + dt.timedelta(interpolation_radius)
    period_index = pd.period_range(start=start_date, end=end_date)

    file_list = locator.daily_file_path(hemisphere, period_index, search_paths)
    if len(file_list) == 0:
        gridset = empty_gridset(hemisphere['shape'], 'D')
    else:
        gridset = _concentration_gridset_by_filelist(file_list)

    metadata = {
        'hemi': hemisphere['short_name'],
        'temporality': 'D',
        'period': pd.Period(date, freq='D'),
        'search_paths': search_paths
    }

    gridset['metadata'].update(metadata)

    return gridset


def concentration_daily_average_over_date_range(nt_hemi,
                                                date_range,
                                                search_paths):

    daily_filename_list = locator.daily_file_paths_in_date_range(nt_hemi,
                                                                 date_range[0],
                                                                 date_range[-1],
                                                                 search_paths)
    daily_filename_list = double_weight_smmr_files(daily_filename_list)

    if len(daily_filename_list) == 0:
        gridset = empty_gridset(nt_hemi['shape'], 'D')
    else:
        gridset = _concentration_average_gridset_from_daily_filelist(daily_filename_list)

    metadata = {
        'hemi': nt_hemi['short_name'],
        'temporality': 'D',
        'search_paths': search_paths
    }

    gridset['metadata'].update(metadata)

    return gridset


def _validate_monthly(func):
    @functools.wraps(func)
    def func_wrapper(*args):
        year, month = args[1:3]
        today = dt.date.today()
        last_day_of_previous_month = today - (dt.timedelta(today.day))
        last_day_of_target_month = dt.date(year, month, cal.monthrange(year, month)[1])

        month_is_valid = (
            nt.BEGINNING_OF_SATELLITE_ERA <= last_day_of_target_month <= last_day_of_previous_month
        )
        if not month_is_valid:
            raise e.YearMonthOutOfRangeError('{}-{:02}'.format(year, month))

        return func(*args)
    return func_wrapper


@_validate_monthly
def concentration_monthly(hemisphere, year, month, search_paths,
                          min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a dict containing the sea ice concentration data for the given year
    and month in the specified hemisphere as a numpy array. The dict also
    includes information about the source files from which the data was read.
    Also check to make sure that the monthly file was created with enough
    daily files.  If a monthly file is not found, but a month's worth of
    daily files exist, create an average from the daily files.

    """
    monthly_file_path = locator.monthly_file_path(hemisphere, year, month, search_paths)

    daily_filename_list = locator.all_daily_file_paths_for_month(
        hemisphere, year, month, search_paths
    )
    daily_filename_list = double_weight_smmr_files(daily_filename_list)

    if len(daily_filename_list) < min_days_for_valid_month:
        log.warn('Insufficient daily files found for {yyyy:04}-{mm:02}; returning empty monthly '
                 'gridset.'.format(yyyy=year, mm=month))
        return empty_gridset(hemisphere['shape'], 'M')

    last_day_of_month = dt.date(year, month, cal.monthrange(year, month)[1])
    should_use_final_data_for_month = last_day_of_month <= nt.LAST_DAY_WITH_VALID_FINAL_DATA

    if monthly_file_path and should_use_final_data_for_month:
        gridset = _concentration_gridset_by_filelist([monthly_file_path])
    else:
        gridset = _concentration_average_gridset_from_daily_filelist(daily_filename_list)

    metadata = {
        'hemi': hemisphere['short_name'],
        'temporality': 'M',
        'period': pd.Period(dt.date(year, month, 1), freq='M'),
        'search_paths': search_paths
    }

    gridset['metadata'].update(metadata)

    return gridset


def concentration_seasonal(hemisphere, year, months, search_paths,
                           min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a dict containing the sea ice concentration data for the given year
    and season in the specified hemisphere as a numpy array. The dict also
    includes information about the source files from which the data was read.
    Also check to make sure that each monthly file used was created with enough
    daily files. If a monthly file is not found, but a month's worth of daily
    files exist, create an average from the daily files.

    """
    def masked_data(np_arr):
        """Return gridset's data with everything outside the valid range masked"""
        return np.ma.masked_outside(np_arr, *nt.VALID_DATA_RANGE)

    def flags_only(np_arr):
        return np.ma.masked_inside(np_arr, *nt.VALID_DATA_RANGE)

    monthly_gridsets = []
    for month in months:
        year_ = year - 1 if month == 12 else year
        log.info('getting monthly concentration {} {}-{:02}'.format(hemisphere['short_name'],
                                                                    year_,
                                                                    month))
        monthly_gridset = concentration_monthly(
            hemisphere,
            year_,
            month,
            search_paths,
            min_days_for_valid_month
        )
        monthly_gridsets.append(monthly_gridset)

    stacked_data = np.dstack([g['data'] for g in monthly_gridsets])
    flag_layer = flag_layer_from_cube(flags_only(stacked_data), nt.FLAGS['missing'])
    data = masked_data(stacked_data).mean(axis=2).filled(flag_layer)

    metadata = {
        'files': [g['metadata']['files'] for g in monthly_gridsets],
        'hemi': hemisphere['short_name'],
        'temporality': 'seasonal',
        'season': (year, months),
        'search_paths': search_paths,
        'valid_data_range': (0.0, 100.0)
    }
    metadata.update(_flags_and_missing())

    gridset = {
        'data': data,
        'metadata': metadata
    }

    return gridset


def flag_layer_from_cube(flag_cube, missing_value=np.nan):
    """Return a single layer of flag values, reduced from a cube of flag values. In
    the returned ndarray, a gridcell is unmasked if and only if that gridcell
    has the same flag value in every layer of the flag_cube.

    If a missing_value is provided, then any layers in the flag_cube that are
    all missing are ignored.

    """
    if len(flag_cube.shape) == 2:
        return flag_cube

    # initalize flag_layer to the first layer that is not all missing (if there
    # is one that is not all missing)
    flag_layer = flag_cube[:, :, 0]
    for i in range(0, flag_cube.shape[2]):
        if not np.all(flag_cube[:, :, i] == missing_value):
            flag_layer = flag_cube[:, :, i].copy()
            break

    for i in range(0, flag_cube.shape[2]):
        if np.all(flag_cube[:, :, i] == missing_value):
            continue

        match = flag_layer == flag_cube[:, :, i]
        match = match.filled(False)

        flag_layer = np.ma.array(flag_layer, mask=~match)

    return flag_layer


def _concentration_average_gridset_from_daily_filelist(daily_filename_list):
    """ Read and average a list of daily files. """
    gridset = _concentration_gridset_by_filelist(daily_filename_list)

    # mask everything but valid data
    missing_value = gridset['metadata']['missing_value']
    data_cube = np.ma.masked_outside(gridset['data'], *gridset['metadata']['valid_data_range'])

    # get cube of nothing but flag values
    flag_cube = np.ma.array(gridset['data'], mask=~data_cube.mask)
    flag_cube = np.ma.masked_equal(flag_cube, missing_value)

    average = cube.average_cube(data_cube)

    flag_layer = flag_layer_from_cube(flag_cube)

    # replace mask with flag values where possible
    averaged_and_flagged = cube.apply_patch(average, flag_layer)

    # replace rest of mask with missing
    new_data = averaged_and_flagged.filled(fill_value=missing_value)

    gridset['data'] = new_data

    return gridset


def concentration_monthly_over_years(hemisphere, start_year, end_year, month, search_paths,
                                     min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing a cube of data for a given month across a
    range of years. The data is ordered by year. The metadata includes the
    month, year range, and list of files from which the data was retrieved.
    """
    year_list = list(range(start_year, end_year + 1))

    gridsets = [concentration_monthly(hemisphere, year, month, search_paths,
                                      min_days_for_valid_month) for year in year_list]

    data = np.ma.dstack([g['data'] for g in gridsets])

    metadata = {}
    metadata['files'] = [g['metadata']['files'] for g in gridsets]

    period_index = pd.PeriodIndex([], freq='M')
    for g in gridsets:
        period_index = period_index.append(g['metadata']['period_index'])
    metadata['period_index'] = period_index

    metadata['valid_data_range'] = gridsets[0]['metadata']['valid_data_range']
    metadata['flags'] = gridsets[0]['metadata']['flags']
    metadata['missing_value'] = gridsets[0]['metadata']['missing_value']

    gridset = {
        'data': data,
        'metadata': metadata
    }

    return gridset


def concentration_seasonal_over_years(hemisphere, start_year, end_year, months, search_paths,
                                      min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing a cube of data for a given month across a
    range of years. The data is ordered by year. The metadata includes the
    month, year range, and list of files from which the data was retrieved.
    """
    year_list = list(range(start_year, end_year + 1))

    gridsets = [concentration_seasonal(hemisphere, year, months, search_paths,
                                       min_days_for_valid_month) for year in year_list]

    data = np.ma.dstack([g['data'] for g in gridsets])

    metadata = {}
    metadata['files'] = [g['metadata']['files'] for g in gridsets]

    metadata['valid_data_range'] = gridsets[0]['metadata']['valid_data_range']
    metadata['flags'] = gridsets[0]['metadata']['flags']
    metadata['missing_value'] = gridsets[0]['metadata']['missing_value']

    gridset = {
        'data': data,
        'metadata': metadata
    }

    return gridset


def empty_gridset(shape, temporality, period=None):

    metadata = {'files': [],
                'empty_gridset': True,
                'temporality': temporality,
                'period_index': pd.PeriodIndex([], freq=temporality),
                'valid_data_range': (0., 100.)}

    if period is not None or temporality == 'D':
        log.debug('creating empty gridset with period {}'.format(period))
        metadata['period'] = period

    metadata.update(_flags_and_missing())

    grid = np.full(shape, metadata['missing_value'], dtype=np.float)

    return {
        'data': grid,
        'metadata': metadata
    }


def extent_daily_median(hemisphere, start_year, end_year, dayofyear=None,
                        search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                        interpolation_radius=0,
                        extent_threshold=nt.EXTENT_THRESHOLD,
                        allow_bad_dates=False):

    date_index = _dateindex_for_dayofyear(start_year, end_year, dayofyear)

    gridsets = [concentration_daily(hemisphere,
                                    date,
                                    search_paths,
                                    interpolation_radius) for date in date_index.date]
    if not allow_bad_dates:
        gridsets = [gf.drop_bad_dates(g) for g in gridsets]
    gridsets = [gf.interpolate(g) for g in gridsets]
    gridsets = [gf.concentration_to_extent(extent_threshold, g) for g in gridsets]

    cube = np.ma.dstack([g['data'] for g in gridsets])
    data = _extent_median(cube, 1, 0, nt.FLAGS['missing'], nt.FLAGS['land'], nt.FLAGS['coast'])

    metadata = {}
    metadata['files'] = [g['metadata']['files'] for g in gridsets]
    metadata['dayofyear'] = dayofyear
    metadata['years'] = sorted(np.unique(date_index.year))
    metadata['period_index'] = [g['metadata']['period_index'] for g in gridsets]

    metadata['valid_data_range'] = gridsets[0]['metadata']['valid_data_range']
    metadata['missing_value'] = gridsets[0]['metadata']['missing_value']
    metadata['flags'] = gridsets[0]['metadata']['flags']

    return {'data': data, 'metadata': metadata}


def extent_monthly_median(hemisphere, start_year, end_year, month,
                          search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                          extent_threshold=nt.EXTENT_THRESHOLD,
                          min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Call extent monthly for all months between start_year and end_year"""

    metadata = {}
    years = np.arange(start_year, end_year+1)
    gridsets = [concentration_monthly(hemisphere, year, month, search_paths,
                                      min_days_for_valid_month) for year in years]
    gridsets = [gf.concentration_to_extent(extent_threshold, g) for g in gridsets]

    cube = np.ma.dstack([g['data'] for g in gridsets])
    data = _extent_median(cube, 1, 0, nt.FLAGS['missing'], nt.FLAGS['land'], nt.FLAGS['coast'])

    metadata['files'] = [g['metadata']['files'] for g in gridsets]
    metadata['years'] = list(years)
    metadata['month'] = month
    metadata['valid_data_range'] = (0, 1)
    metadata.update(_flags_and_missing())

    gridset = {'data': data, 'metadata': metadata}

    return gridset


def _extent_median(cube, ice=1, ocean=0,
                   missing=nt.FLAGS['missing'],
                   land=nt.FLAGS['land'],
                   coast=nt.FLAGS['coast']):
    """Returns a grid with median ice extent from a cube containing ice extent
    grids. Coast and missing are replaced with land.

    """

    ice_extent = np.median(np.where(cube > ice, 0, cube), axis=2) >= 0.5
    ice_or_ocean = np.where(ice_extent, ice, ocean)
    always_land = np.all(np.in1d(cube, [land, missing, coast]).reshape(cube.shape), axis=2)
    return np.where(always_land, land, ice_or_ocean)


def _dateindex_for_dayofyear(start_year, end_year, dayofyear):
    """Return a Pandas DateIndex of dates for the day of year on each year between
       start_year and end_year.

    """

    date_index = pd.date_range(
        start=dt.date(start_year, 1, 1),
        end=dt.date(end_year, 12, 31),
        freq='D'
    )

    if dayofyear == 366:
        date_index = date_index[date_index.dayofyear == 1] + pd.Timedelta(365, unit='d')
    else:
        date_index = date_index[date_index.dayofyear == dayofyear]

    return date_index


def _scale_valid_data(nd_arr, valid_range, scale):
    valid_data = np.ma.masked_outside(nd_arr, *valid_range)
    scaled = valid_data / scale
    return scaled.data


def _period_index_from_file_list(file_list):
    periods = []
    for file_ in file_list:
        match = nt.DATA_FILENAME_MATCHER.search(file_)
        year = match.group('year')
        month = match.group('month')
        day = match.group('day')
        period_str = '-'.join([p for p in [year, month, day] if p is not None])

        freq = 'M' if day is None else 'D'
        periods.append(pd.Period(period_str, freq=freq))

    freqstrs = list(set(period.freqstr for period in periods))
    if len(freqstrs) == 1:
        freq = freqstrs[0]
    else:
        raise e.SeaIceDataException('Could not infer frequency from file list {}; found '
                                    '{}'.format(file_list, freqstrs))

    period_index = pd.PeriodIndex(periods, freq=freq)

    return period_index


def _concentration_gridset_by_filelist(file_list):
    """Return a gridset object for a list of files.

    A gridset is a dictionary with two keys 'data' and 'metadata'.

    'data' holds either a 2D or 3D masked numpy array.

    'metadata' holds a dictionary with a single key 'files' which holds the
    filelist that was used to get the data.

    """
    data_list = [_read_goddard_nasateam_file(file_) for file_ in file_list]

    period_index = _period_index_from_file_list(file_list)

    data_cube = np.ma.dstack(data_list)
    scaled_data_cube = _scale_valid_data(data_cube, nt.VALID_DATA_RANGE, nt.SCALE)
    metadata = {'files': file_list,
                'period_index': period_index,
                'valid_data_range': (nt.VALID_DATA_RANGE[0] / nt.SCALE,
                                     nt.VALID_DATA_RANGE[1] / nt.SCALE)}
    metadata.update(_flags_and_missing())

    return {
        'data': np.ma.squeeze(scaled_data_cube),
        'metadata': metadata
    }


def _read_goddard_nasateam_file(filename):
    with open(filename, 'rb') as fp:
        rows, cols = _rows_columns_from_goddard_nasateam_header(fp.read(nt.NASATEAM_HEADER_LENGTH))
        data = (np.fromfile(fp, dtype=np.uint8)).reshape(rows, cols)
    return data


def _parse_goddard_nasateam_header(header):
    parsed = np.fromstring(header, dtype=np.dtype(nt.NASATEAM_HEADER))
    return parsed


def _rows_columns_from_goddard_nasateam_header(header):
    parsed = _parse_goddard_nasateam_header(header)
    return (parsed['grid_rows'].astype(np.uint16)[0],
            parsed['grid_cols'].astype(np.uint16)[0])


def double_weight_smmr_files(paths):
    """Returns the given list of filenames with each SMMR filename appearing an
    additional time in the list. SMMR files are determined based on the constant
    nt.SMMR_PLATFORM.

    """
    double_weighted = []
    for f in paths:
        match = re.match(nt.DATA_FILENAME_MATCHER, f)
        if match.group('platform') == nt.SMMR_PLATFORM:
            double_weighted.append(f)

    return sorted(paths + double_weighted)


def _flags_and_missing():
    """Returns a dict of the nasateam standard values of 'flags' and 'missing_value' """
    flags = copy.deepcopy(nt.FLAGS)
    missing = flags.pop('missing', None)
    return {'flags': flags,
            'missing_value': missing}
