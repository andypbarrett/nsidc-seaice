import copy
import datetime as dt
from functools import lru_cache
from functools import partial
import logging
import re
from multiprocessing.pool import ThreadPool

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import api
from . import getter
from . import gridset_filters as gf
from . import locator
import seaice.nasateam as nt

log = logging.getLogger(__name__)


MAXIMUM_F_TEST_P_VALUE = .05


def trend_gridset(nt_hemi, year, month, search_paths,
                  min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
                  trend_start_year=None, *, clipping_threshold):
    dates = _datetime_index_for_trends(year, month, start_year=trend_start_year)
    start_year = dates[0].year
    end_year = dates[-1].year

    std_gridset = _daily_std_gridset_for_trends(nt_hemi, year, month, search_paths,
                                                min_days_for_valid_month, trend_start_year)
    std_cube = std_gridset['data']
    weight_cube = _weight_from_std(std_cube)

    invalid_ice_mask = nt.invalid_ice_mask(nt_hemi, month)
    stacked_gridset = getter.concentration_monthly_over_years(nt_hemi,
                                                              start_year,
                                                              end_year,
                                                              month,
                                                              search_paths)
    stacked_gridset = gf.apply_filters(stacked_gridset,
                                       [partial(gf.drop_invalid_ice, invalid_ice_mask),
                                        gf.apply_largest_pole_hole])
    stacked_valid_data = stacked_gridset['metadata']['valid_data_range']

    concentration_cube = np.ma.masked_outside(
        stacked_gridset['data'], *stacked_valid_data).filled(np.nan)

    trend_grid = _trend_grid(concentration_cube, weight_cube,
                             clipping_threshold=clipping_threshold)

    # TODO: Instead of having flags and data in one array, consider splitting
    # them in to two arrays, e.g.:
    # std_gridset['data'] has 0-100 and NaN for flag/fill values, and
    # std_gridset['flagdata'] has 251+ flag values and NaNs for data.
    flag_layer = getter.flag_layer_from_cube(np.ma.masked_inside(stacked_gridset['data'],
                                                                 *stacked_valid_data),
                                             stacked_gridset['metadata']['missing_value'])

    data = np.where(flag_layer.mask, trend_grid, flag_layer)

    metadata = {}

    flags = copy.deepcopy(nt.FLAGS)
    flags.pop('missing')
    metadata['flags'] = flags

    valid_data_min = (stacked_gridset['metadata']['valid_data_range'][0] -
                      stacked_gridset['metadata']['valid_data_range'][1])
    valid_data_max = (stacked_gridset['metadata']['valid_data_range'][1] -
                      stacked_gridset['metadata']['valid_data_range'][0])
    metadata['valid_data_range'] = (valid_data_min, valid_data_max)

    metadata['hemi'] = nt_hemi['short_name']
    metadata['period'] = pd.Period('{}-{}'.format(year, month), freq='M')
    metadata['search_paths'] = search_paths
    metadata['temporality'] = 'M'
    metadata['type'] = 'Monthly Trend'
    metadata['missing_value'] = stacked_gridset['metadata']['missing_value']

    metadata['std'] = std_gridset['metadata']
    metadata['monthly'] = stacked_gridset['metadata']
    metadata['filename'] = stacked_gridset['metadata']['files'][-1]

    metadata['data'] = {
        'concentration': concentration_cube,
        'weight': weight_cube,
        'std': std_cube,
        'flag_layer': flag_layer,
        'trend_grid': trend_grid,
        'stacked_data': stacked_gridset['data']
    }

    gridset = {'data': data, 'metadata': metadata}

    return gridset


def seasonal_trend_gridset(nt_hemi, year, season, search_paths, seasons,
                           min_days_for_valid_month, *, clipping_threshold):
    nt.validate_seasons(seasons)
    months = seasons[season]
    dates = nt.datetime_index_for_seasonal_trends(year, tuple(months))
    start_year = dates[0].year

    season_crosses_year_boundary = months[0] > months[-1]
    if season_crosses_year_boundary:
        start_year = start_year + 1

    end_year = dates[-1].year

    std_gridset = _daily_std_gridset_for_seasonal_trends(nt_hemi, end_year, months, search_paths,
                                                         min_days_for_valid_month)
    std_cube = std_gridset['data']
    weight_cube = _weight_from_std(std_cube)

    invalid_ice_mask = np.all(np.dstack([nt.invalid_ice_mask(nt_hemi, m) for m in months]), axis=2)

    stacked_gridset = getter.concentration_seasonal_over_years(nt_hemi,
                                                               start_year,
                                                               end_year,
                                                               months,
                                                               search_paths)

    stacked_gridset = gf.apply_filters(stacked_gridset,
                                       [partial(gf.drop_invalid_ice, invalid_ice_mask),
                                        gf.apply_largest_pole_hole])
    stacked_valid_data = stacked_gridset['metadata']['valid_data_range']

    concentration_cube = np.ma.masked_outside(
        stacked_gridset['data'], *stacked_valid_data).filled(np.nan)

    trend_grid = _trend_grid(concentration_cube, weight_cube,
                             clipping_threshold=clipping_threshold)

    flag_layer = getter.flag_layer_from_cube(np.ma.masked_inside(stacked_gridset['data'],
                                                                 *stacked_valid_data),
                                             stacked_gridset['metadata']['missing_value'])

    data = np.where(flag_layer.mask, trend_grid, flag_layer)

    metadata = {}

    flags = copy.deepcopy(nt.FLAGS)
    flags.pop('missing')
    metadata['flags'] = flags

    valid_data_min = (stacked_gridset['metadata']['valid_data_range'][0] -
                      stacked_gridset['metadata']['valid_data_range'][1])
    valid_data_max = (stacked_gridset['metadata']['valid_data_range'][1] -
                      stacked_gridset['metadata']['valid_data_range'][0])
    metadata['valid_data_range'] = (valid_data_min, valid_data_max)

    metadata['hemi'] = nt_hemi['short_name']
    metadata['search_paths'] = search_paths
    metadata['temporality'] = 'M'
    metadata['type'] = 'Seasonal Trend'
    metadata['missing_value'] = stacked_gridset['metadata']['missing_value']

    metadata['std'] = std_gridset['metadata']
    metadata['monthly'] = stacked_gridset['metadata']
    metadata['filename'] = stacked_gridset['metadata']['files'][-1]

    metadata['data'] = {
        'concentration': concentration_cube,
        'weight': weight_cube,
        'std': std_cube,
        'flag_layer': flag_layer,
        'trend_grid': trend_grid,
        'stacked_data': stacked_gridset['data']
    }

    gridset = {'data': data, 'metadata': metadata}

    return gridset


def _daily_std_gridset_for_trends(nt_hemi, year, month, search_paths,
                                  min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
                                  trend_start_year=None):
    """Returns a gridset of monthly standard deviations. gridset['data'] is a cube
    of standard deviations (i,j,k) [column, row, year], such that each layer(k)
    contains the standard deviations for a single year. Each gridcell's standard
    deviation (i,j), is computed from the standard deviation of the
    concentrations of all the daily concentration values for the month (1-31) at
    location (i,j).

    nt_hemi: nt.NORTH or nt.SOUTH

    year: int. get standard deviations for data starting in 1978 or 1979, and
          ending in this year

    month: int, 1-12

    search_paths: directories for 0051 and 0081 files

    """
    date_index = _datetime_index_for_trends(year, month, start_year=trend_start_year)

    # list of tuples sorted by year; (year, date_index[date_index.year == year])
    dates_by_year = sorted(date_index.groupby(date_index.year).items())

    data_list = []
    metadata = {'files': [], 'period_indexes': []}

    for year, dates in dates_by_year:
        daily_filename_list = locator.all_daily_file_paths_for_month(
            nt_hemi, year, month, search_paths
        )
        daily_filename_list = getter.double_weight_smmr_files(daily_filename_list)

        if len(daily_filename_list) >= min_days_for_valid_month:
            std_gridset = _std_gridset(nt_hemi, dates)

            data_list.append(std_gridset['data'])
            metadata['files'].append(std_gridset['metadata']['files'])
            metadata['period_indexes'].append(std_gridset['metadata']['period_index'])
        else:
            log.warn('Insufficient daily files found for {yyyy:04}-{mm:02}; appending grid layer '
                     'filled with np.nan.'.format(yyyy=year, mm=month))
            data_list.append(np.full(nt_hemi['shape'], np.nan))

    data = np.dstack(data_list)

    return {'data': data, 'metadata': metadata}


def _daily_std_gridset_for_seasonal_trends(nt_hemi, year, months, search_paths,
                                           min_days_for_valid_month):
    date_index = nt.datetime_index_for_seasonal_trends(year, tuple(months))

    # since winter is defined as December-February, count December as part of
    # the next year; also count months if a custom definition for winter is used
    # that could include, for example, November
    groupby_years = [(d.year + 1 if d.month > months[-1] else d.year) for d in date_index]

    # list of tuples sorted by year; (year, date_index[date_index.year == year])
    dates_by_year = sorted(date_index.groupby(groupby_years).items())

    data_list = []
    metadata = {'files': [], 'period_indexes': []}

    for year, dates in dates_by_year:
        std_gridset = _std_gridset(nt_hemi, dates)
        data_list.append(std_gridset['data'])
        metadata['files'].append(std_gridset['metadata']['files'])
        metadata['period_indexes'].append(std_gridset['metadata']['period_index'])

    data = np.dstack(data_list)

    return {'data': data, 'metadata': metadata}


@lru_cache(maxsize=16)
def _datetime_index_for_trends(end_year, month, start_year=None):
    if start_year is None or dt.date(start_year, 1, 1) < nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY:
        start_date = nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY
    else:
        start_date = dt.date(start_year, 1, 1)

    first_of_current_month = dt.date.today().replace(day=1)
    last_day_of_previous_month = first_of_current_month - dt.timedelta(1)

    dates = pd.date_range(start=start_date, end=last_day_of_previous_month)
    dates = dates[dates.month == month]
    dates = dates[dates.year <= end_year]

    return dates


def _gridset_matches_platform(gridset, pattern, platform):
    """Returns True if the given gridset contains any files matching the given platform.

    gridset: gridset with metadata; the metadata has a list of files (no nested
             lists)

    pattern: regex matching file names in gridset['metadata']['files'], with a
             "platform" capture group

    platform: the platform to match

    """
    for file_ in gridset['metadata']['files']:
        match = re.match(pattern, file_)
        if match.group('platform') == platform:
            return True
    return False


def _std_gridset(nt_hemi, dates):
    list_of_dailies = []

    metadata = {'files': [], 'period_index': pd.PeriodIndex([], freq='D')}

    valid_data_range = None

    for date in dates:
        daily_gridset = api.concentration_daily(nt_hemi,
                                                date.year,
                                                date.month,
                                                date.day,
                                                allow_bad_dates=False,
                                                drop_invalid_ice=True)

        empty = daily_gridset['metadata'].get('empty_gridset', False)
        if empty:
            continue

        list_of_dailies.append(daily_gridset['data'])
        metadata['files'].append(daily_gridset['metadata']['files'])

        period_index = daily_gridset['metadata']['period_index']
        metadata['period_index'] = metadata['period_index'].append(period_index)

        valid_data_range = daily_gridset['metadata']['valid_data_range']

        # double weight smmr files, mainly matters for August 1987
        if _gridset_matches_platform(daily_gridset, nt.DATA_FILENAME_MATCHER, nt.SMMR_PLATFORM):
            list_of_dailies.append(daily_gridset['data'])
            metadata['files'].append(daily_gridset['metadata']['files'])

    cube_of_dailies = np.ma.dstack(list_of_dailies)
    cube_of_dailies = np.ma.masked_outside(cube_of_dailies, *valid_data_range)

    data = cube_of_dailies.std(axis=2)

    gridset = {'data': data, 'metadata': metadata}

    return gridset


def _trend_gridcell(concentrations, weights, *, clipping_threshold):
    """Calculate the the decadal trend (average change or slope).

    To get the single-year trend, we calculate a WLS line of best fit, where
    "x" is time in years. Since the slope represents the average annual change,
    we must multiply by 10 to get the decadal change.
    """
    nonzero_weights = (weights != 0)

    # skip gridcells that don't have enough points to perform a linear
    # regression
    if np.sum(nonzero_weights) < 3:
        return 0

    y = concentrations
    x = np.arange(y.size)
    w = weights

    # cut out any years for this gridcell with zero weight
    y = y[nonzero_weights]
    x = x[nonzero_weights]
    w = w[nonzero_weights]

    # > Since we want a linear model that looks like y ~ β_1*x + β_0, we
    # > need to add an extra array or vector of ones to our independent
    # > variable, df.Tobacco because the statsmodels OLS() function does not
    # > assume that we would like a constant or intercept intercept term,
    # > β_0. This is not so uncommon as it would seem; several regression
    # > packages make this requirement.
    #
    # http://connor-johnson.com/2014/02/18/linear-regression-with-python/
    #
    # Additionally, this matches the algorithm used in the code for V2 of
    # the Sea Ice Index:
    #  https://bitbucket.org/nsidc/seaice_projects/src/v2.0.0/source/seaice_index/idl/
    x = sm.add_constant(x)

    # "WLS" = "Weighted Least Squares"
    result = sm.WLS(y, x, weights=w).fit()

    # reject the computed trend if the uncertainty is too high
    if result.f_pvalue > MAXIMUM_F_TEST_P_VALUE:
        return 0

    # concentration change per year
    slope = result.params[1]
    # concentration change per decade
    slope = slope * 10

    # Apply clipping after calculating the final decadal trend value
    if slope > clipping_threshold:
        return clipping_threshold

    if slope < -clipping_threshold:
        return -clipping_threshold

    return slope


def _trend_grid(concentration_cube, weight_cube, *, clipping_threshold):
    """Build a grid for a decadal trend."""
    assert concentration_cube.shape == weight_cube.shape
    assert clipping_threshold

    rows, cols, periods = weight_cube.shape

    # Flatten rows and cols of the concentration/weight cubes
    # A shape of (448, 304, 41) becomes (136192, 41)
    flattened_concentration_cube = concentration_cube.reshape((rows * cols, periods))
    flattened_weight_cube = weight_cube.reshape((rows * cols, periods))

    fn = partial(_trend_gridcell, clipping_threshold=clipping_threshold)
    args = zip(flattened_concentration_cube, flattened_weight_cube)
    with ThreadPool() as p:
        results = p.starmap(fn, args)

    trend_grid = np.array(results).reshape(rows, cols)

    return trend_grid


def _weight_from_std(std):
    """Returns an array of weight values from an array of standard deviation
    values. Weights are calculated as 1/std^2. Values of 0 in the given std
    array are given 0 weight.

    """

    # avoid division by zero
    std = np.where(std == 0, np.nan, std)

    weights = 1 / std**2

    # convert NaN to 0
    weights = np.nan_to_num(weights)

    return weights
