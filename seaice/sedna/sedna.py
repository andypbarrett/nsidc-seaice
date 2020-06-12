"""Compute statistics of sea ice concentration cubes
"""
import copy
from datetime import date as dt_date
from functools import lru_cache
import os
import re

import numpy as np
import pandas as pd
import logging

import seaice.data as sid
import seaice.datastore as sds
from .cube import ConcentrationCube as Cube
import seaice.nasateam as nt

log = logging.getLogger(__name__)


def _sea_ice_statistics(gridset, period, config, failed_qa=None):
    """Given a seaicedata gridset, a pandas.Period, and a config dict, return a
    dictionary containing statistics and some metadata.

    Positional Arguments:
    ---------------------
    gridset: gridset with data and metadata, like one retrieved from seaice.data

    period: pandas.Period, with frequency either day or month.

    config: dict containing:
        hemisphere: nt.NORTH or nt.SOUTH
        extent_threshold: cutoff value for extent
        grid_areas: grid whose shape matches a layer of the data in gridset,
                    whose values are the areas of the grid cells in square km

    failed_qa: optional boolean value to use as default for 'failed qa' field,
               if not present or None, no failed_qa will be returned from the
               statistics row.

    """
    hemisphere = config['hemisphere']
    cube = _get_cube(gridset, period, config)
    total_extent_km2 = cube.extent()
    total_area_km2 = cube.area()
    missing_km2 = cube.missing()

    regional_masks = _fetch_regional_config(config)
    regional_stats = _get_regional_stats(cube, regional_masks, hemisphere, period)

    row = _create_row(
        (period, hemisphere['short_name']), total_extent_km2, total_area_km2, missing_km2,
        gridset['metadata'], regional_stats, failed_qa)
    return row


def _get_cube(gridset, period, config):

    hemisphere = config['hemisphere']
    extent_threshold = config['extent_threshold']
    grid_areas = config['grid_areas']

    missing_value = gridset['metadata']['missing_value']
    valid_data_range = gridset['metadata']['valid_data_range']
    flags = gridset['metadata']['flags']

    invalid_ice_mask = nt.invalid_ice_mask(hemisphere, period.month)

    return Cube(gridset['data'],
                missing_value=missing_value, invalid_data_mask=invalid_ice_mask,
                grid_areas=grid_areas, extent_threshold=extent_threshold,
                valid_data_range=valid_data_range, flags=flags)


def _set_failed_qa_flag(frame, eval_days, regression_delta_km2):
    """Given a frame of total extent and failed_qa; regression_delta_km2, and a number of
       eval days evaluate the frame based on a simple linear regression and return
       a frame with 'failed_qa' marked appropriately.

       Evaluation will interpolate on the fly - meaning that if a day in a series
       is marked bad the next day will be evaluated with the previously marked
       day filled in with an interpolated value based on the evaluation frame.

       Positional Arguments:
       ---------------------
       frame:                 Pandas dataframe with total_extent_km2 and failed_qa columns
       eval_days:             Number of days to evaluate the linear regression
       regression_delta_km2:  Maximum difference in value between the value expected by
                              the regression and the actual value.
       """

    update_frame = frame.copy()

    for period in update_frame.index[eval_days:]:
        filename = update_frame['filename'].loc[period]
        if filename == []:
            update_frame.at[period, 'failed_qa'] = False
            continue

        period_total_extent_km2 = update_frame['total_extent_km2'].loc[period]
        poly_fit_series = update_frame['total_extent_km2'][period-eval_days:period]
        delta = _poly_fit_delta(poly_fit_series)

        if np.isnan(period_total_extent_km2) or abs(delta) > regression_delta_km2:
            update_frame.at[period, 'total_extent_km2'] = np.nan
            update_frame.at[period, 'failed_qa'] = True
        elif not np.isnan(delta):
            update_frame.at[period, 'failed_qa'] = False
    return update_frame


def _poly_fit_delta(data_series_in):
    """Given an input Pandas Series (data_series_in) with a PeriodIndex and at
       least 3 non-nan values, models the expected last value of the series and
       returns the difference between the modeled and actual value.

       A linear regression is computed for the input data_series_in excluding the last value
       and is used to compute the expected value at data_series_in[-1].

       Returns the difference of the actual - expected value, or np.nan if
       regression cannot be performed.

    """
    data_series = data_series_in.copy()
    target = data_series[-1:]
    data_series = data_series[:-1]
    data_series = data_series.dropna()

    if len(data_series) < 2:
            log.warn('Cannot calculate regression fit difference for '
                     '{} without at least 2 previous days data.   Skipping.'.format(target))
            return np.nan
    x_values = [np.float(v.to_timestamp().to_julian_date()) for v in data_series.index.values]
    poly = np.polyfit(x_values, data_series, 1)
    log.debug('poly %s', poly)
    expected_value = target.index.values[0].to_timestamp().to_julian_date() * poly[0] + poly[1]
    return target.values[0] - expected_value


def _get_extent(date, config):
    extent_grid = sid.extent_daily(hemisphere=config['hemisphere'],
                                   year=date.year, month=date.month, day=date.day,
                                   search_paths=config['search_paths'],
                                   interpolation_radius=0)['data']
    return np.sum(((extent_grid == 1) * config['grid_areas']))


def _get_concentration(date, config):
    return sid.concentration_daily(hemisphere=config['hemisphere'],
                                   year=date.year, month=date.month, day=date.day,
                                   search_paths=config['search_paths'],
                                   interpolation_radius=0)


def merge_daily_datastore_with_validation_dataframe(validation_frame, data_store):
    """Given a validation dataframe and a data store location update the
       datastore with the new validation information"""
    frame = _dataframe_from_data_store_daily(data_store)
    frame.update(validation_frame)
    columns = frame.columns.tolist()
    sds.write_daily_datastore(frame, columns, data_store)


def get_validation_frame(dates, data_store, hemisphere, regression_delta_km2, eval_days):
    """Returns a validation frame (multiindexed dataframe with 'seaice_extent_km2' and
    failed_qa columns).

    Parameters:
        dates: Pandas period range to evaluate
        data_store: Location to load the sedna datastore from
        hemisphere:  Hemisphere to work with
        regression_delta_km2:  Maximum delta to allow when evaluating the data against
                           the regression fit
        eval_days: How many prior days to use when calculating the linear regression
    """

    frame = _dataframe_from_data_store_daily(data_store)
    validation_frame = _create_validation_frame(dates, frame.copy(), hemisphere,
                                                eval_days, regression_delta_km2)
    return validation_frame


def update_sea_ice_statistics_daily(dates, config, validate_data=True):
    """Update total sea ice extent and area in the datastore for a set of dates,
       run validation and update QA flag as appropriate for NRT data.

       Parameters:
       dates:           List of dates to return statistics for
       config:          Sedna configuration dict
       validate_data :  bool to set if the data should run validation.  Defaults
                        to True

       Returns a bool indicating if the updates occurred without validation failures

    """
    columns = _column_names(config)

    data_store = config.get('data_store', 'daily.p')
    df = _dataframe_from_data_store_daily(data_store)
    df = _add_columns_to_dataframe(df, columns)

    default_failed_qa_value = False if validate_data else None

    new_rows = dict()
    for date in dates:
        gridset = sid.concentration_daily(hemisphere=config['hemisphere'],
                                          year=date.year, month=date.month, day=date.day,
                                          search_paths=config['search_paths'],
                                          interpolation_radius=config['interpolation_radius'])

        new_rows.update(_sea_ice_statistics(gridset, date, config,
                        failed_qa=default_failed_qa_value))
        log.info('stats for {hemi} {date}'.format(
            hemi=config['hemisphere']['short_name'],
            date=date.to_timestamp().date().isoformat()))

    new_values = pd.DataFrame().from_dict(new_rows, orient='index')
    new_values.index.names = ['date', 'hemisphere']

    # Drop any rows of the original df that are in the new new_values.
    df = df.drop(new_values.index, errors='ignore')
    df = df.append(new_values)

    sds.write_daily_datastore(df, columns, data_store)

    # Skip validation if validation flag not set
    if not validate_data:
        return True

    # Get frame of the right size to evaluate
    validation_frame = _create_validation_frame(dates, df.copy(),
                                                config['hemisphere']['short_name'],
                                                config['eval_days'],
                                                config['regression_delta_km2'])
    if len(validation_frame) > 0:
        merge_daily_datastore_with_validation_dataframe(validation_frame,
                                                        config.get('data_store', 'daily.p'))
    return len(validation_frame[validation_frame['failed_qa']]) == 0


def sea_ice_statistics_monthly(config):
    """Update total sea ice extent and area in the datastore for all months.
    """
    columns = _column_names(config, monthly=True)

    data_store = config.get('data_store', 'monthly.p')
    df = _dataframe_from_data_store_monthly(data_store)
    df = _add_columns_to_dataframe(df, columns)

    daily_df = _daily_df_for_monthly_statistics(config)

    # get averages of the daily values in each month
    grouped = daily_df.groupby([daily_df.index.year, daily_df.index.month])
    means = grouped.mean()  # MultiIndex: [year, month]

    means['filename'] = [None] * len(means.index)
    means['source_dataset'] = [None] * len(means.index)
    means['hemisphere'] = [config['hemisphere']['short_name']] * len(means.index)

    # set all missing to 0
    for column in [col for col in means.columns if re.match('^.*missing.*$', col)]:
        means[column] = [0] * len(means.index)

    # set months with insufficient data to 0 extent and area, with the full
    # region counted as missing; set source_dataset and filename correctly
    for year_month, df_ in grouped:
        year, month = year_month

        extents = df_['total_extent_km2']
        extent_not_missing = ~extents.isnull()
        valid_days_count = extent_not_missing.sum()

        empty_month = valid_days_count < nt.MINIMUM_DAYS_FOR_VALID_MONTH

        # get the values as derived from the _empty_grid
        if empty_month:
            for key, val in _missing_row(year_month, config['hemisphere']).items():
                means.loc[year_month, key] = val

            means.at[year_month, 'source_dataset'] = []
            means.at[year_month, 'filename'] = []
        else:
            # source_dataset
            dataset = df_.source_dataset.dropna().unique()[0]
            means.at[year_month, 'source_dataset'] = dataset

            # filename; combine all the daily filenames
            filenames = []
            for filename in df_.filename.values:
                filenames += filename
            means.at[year_month, 'filename'] = filenames

    # months with bad concentration due to the size of the pole hole changing
    # within a month should have area set to NaN; the pole hole is completely
    # encompassed by the "central arctic" region, so that is the only region
    # that can be affected by the pole hole changing size, and will be the only
    # region set to NaN
    for year, month, nt_hemi in nt.BAD_CONCENTRATION_MONTHS:
        if config['hemisphere'] != nt_hemi:
            continue
        means.at[(year, month), 'total_area_km2'] = np.nan
        means.at[(year, month), 'meier2007_centralarctic_area_km2'] = np.nan

    # change means' year-month multiindex into month-hemisphere multiindex to
    # match the datastore format
    means['month'] = means.apply(lambda x: pd.Period(year=x.name[0], month=x.name[1], freq='M'),
                                 axis=1)
    means = means.set_index(['month', 'hemisphere'], drop=False)
    means = means[columns]

    df = df.drop(means.index, errors='ignore')
    df = df.append(means)
    df = df[columns]

    sds.write_monthly_datastore(df, columns, data_store)


def _daily_df_for_monthly_statistics(config):
    # get daily dataframe for the appropriate hemisphere, starting from
    # 1978-11-01

    hemi = config['hemisphere']['short_name']

    default_data_store = os.path.join(
        os.path.dirname(config.get('data_store', 'monthly.p')),
        'daily.p'
    )
    data_store = config.get('daily_data_store', default_data_store)

    df = _dataframe_from_data_store_daily(data_store)

    df = df.reset_index()
    df = df[df['hemisphere'] == hemi]
    df = df.set_index(['date'])

    # cut off the days for incomplete months
    today = dt_date.today()
    index = pd.period_range(start=nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY, end=today, freq='D')
    index = index[:-today.day]
    df = df[(index[0] <= df.index) & (df.index <= index[-1])]

    # double weight SMMR days; mainly matters for August 1987
    start, end = nt.PLATFORM_RANGES['n07'][0]
    smmr_df = df[(start <= df.index) & (df.index <= end)]
    df = df.append(smmr_df).sort_index()

    return df


def _missing_row(year_month, nt_hemi):
    year, month = year_month

    gridset = sid.getter.empty_gridset(nt_hemi['shape'], 'M')
    period = pd.Period(year=year, month=month, freq='M')
    config = {
        'hemisphere': nt_hemi,
        'grid_areas': nt_hemi['grid_areas'],
        'extent_threshold': 15
    }
    row = _sea_ice_statistics(gridset, period, config, failed_qa=None)

    vals = list(row.values())[0]
    vals['filename'] = None
    vals['source_dataset'] = None
    vals['hemisphere'] = nt_hemi['short_name']

    return vals


def _add_columns_to_dataframe(df_in, columns, fill_value=np.nan):
    """Return a copy of the given dataframe that also includes specified columns.
    If the dataframe is indexed, the index names will not be added as additional
    columns if they are listed in the input columns.

    Positional Arguments:
    ---------------------
    df_in: Pandas.DataFrame. This dataframe is copied, columns are added to the
        copy, and it is returned.
    columns: Iterable of strings. Column names to add to the dataframe.

    Keyword Arguments:
    ---------------------
    fill_value: The value to assign to the rows for each new column. Defaults
        to np.nan.

    """

    df = df_in.copy()

    new_columns = set(columns) - set(df.columns) - set(df.index.names)
    for col in new_columns:
        df[col] = fill_value

    return df


def _add_regional_columns(cols=[], regional_masks=[]):
    columns = copy.deepcopy(cols)
    for regional_mask in regional_masks:
        for region_name, value in regional_mask['regions'].items():
            for stat in ['extent', 'area', 'missing']:
                column = '{mask}_{region}_{stat}_km2'.format(mask=regional_mask['name'],
                                                             region=region_name,
                                                             stat=stat)
                columns.append(column)

    return columns


def _column_names(config, monthly=False):
    """Return the list of columns for the output datastore."""
    columns = nt.DAILY_DEFAULT_COLUMNS
    if monthly:
        columns = nt.MONTHLY_DEFAULT_COLUMNS
    columns = _add_regional_columns(columns, _fetch_regional_config(config))
    return columns


def _create_row(key, total_extent_km2, total_area_km2, missing_km2, metadata,
                regional_stats=[], failed_qa=None):

    vals = {
        'total_area_km2': _format_areal_value(total_area_km2),
        'total_extent_km2': _format_areal_value(total_extent_km2),
        'missing_km2': _format_areal_value(missing_km2),
        'filename': metadata['files'],
        'source_dataset': _source_dataset(metadata['files']),
    }

    # only add a failed_qa value if one was provided.
    if failed_qa is not None:
        vals.update({'failed_qa': failed_qa})

    for name, extent, area, missing in regional_stats:
        vals[name + '_area_km2'] = _format_areal_value(area)
        vals[name + '_extent_km2'] = _format_areal_value(extent)
        vals[name + '_missing_km2'] = _format_areal_value(missing)

    return {key: vals}


def _dataframe_from_data_store_daily(data_store):
    """Read dataframe from CSV file or create a new empty dataframe.

    We set the index to be a multiindex of date + hemisphere in order to have
    unique values because sea ice statistics exist in both hemispheres.

    """
    try:
        return sds.daily_dataframe(data_store)
    except sds.seaicedatastore.SeaicedatastoreDataStoreNotFoundError:
        return sds.new_daily_dataframe()


def _dataframe_from_data_store_monthly(data_store):
    try:
        return sds.monthly_dataframe(data_store)
    except sds.seaicedatastore.SeaicedatastoreDataStoreNotFoundError:
        return sds.new_monthly_dataframe()


def _fetch_regional_config(config):
    """Returns a dict containing a regional mask configuration. If the config
    contains one, that will be returned, otherwise configuration for the default
    regional mask (Meier's 2007 arctic mask) is returned.

    """
    return config.get('regional_masks', nt.DEFAULT_REGIONAL_MASKS)


def _format_areal_value(km2):
    """Round floating point data to 3 decimals

    Just a helper to format the computed statistics.  But we also handle the
    case where the value is masked that arises when a grid is created from an
    empty gridset.

    """
    try:
        return np.round(km2, 3)
    except AttributeError:
        return np.nan


def _get_regional_stats(cube, regional_masks, hemisphere, period):
    """Return an array of tuples containing the name, extent, area, and missing
    values for a particular region. "regional_masks" is an array of dicts,
    defined in configuration. See the sedna.cli docstrings for configuration
    details.

    """
    regional_stats = []

    for regional_mask in regional_masks:
        # skip over regional masks for the wrong hemisphere
        if regional_mask['hemisphere'] != hemisphere['long_name']:
            continue

        grid_mask = np.fromfile(regional_mask['file'], dtype=np.uint8).reshape(cube.grid_shape())

        for region_name, value in regional_mask['regions'].items():
            name = '{mask}_{region}'.format(mask=regional_mask['name'], region=region_name)

            # numpy Mask, i.e., a Boolean array with False in the region of
            # interest, True everywhere else
            region_mask = (grid_mask != value)

            # True means valid ice can exist on that gridcell, and the gridcell
            # is in the region of interest
            valid_regional_ice = np.logical_and(~region_mask, ~cube.invalid_data_mask)

            extent = cube.extent(region_mask)
            area = cube.area(region_mask)
            missing = cube.missing(region_mask)

            # on days where valid ice is expected, but the region is fully
            # covered by the climatology, set the extent/area/missing to 0; the
            # climatology mask means that no ice should be possible there. For
            # other days, like in the SMMR period where every other day is
            # missing, we don't want to fill in 0 for extent/area when they are
            # correctly set to NaN
            daily = period.freqstr == 'D'
            region_covered_by_climatology_mask = not np.any(valid_regional_ice)

            def _day_with_ice():
                is_smmr_day = period in nt.SMMR_DAYS
                after_smmr = nt.SMMR_DAYS[-1] < period
                return (is_smmr_day or after_smmr)

            zero_day = daily and region_covered_by_climatology_mask and _day_with_ice()

            if zero_day:
                _warn(name, period.year, period.month)
                extent = 0
                area = 0
                missing = 0

            regional_stats.append((name, extent, area, missing))

    return regional_stats


# use a cached function so that the warning does not repeat for every day in the
# month
@lru_cache(maxsize=None)
def _warn(region, year, month):
    log.warn('The region {region} is completely masked out by the '
             'invalid data mask for {year:04}-{month:02}. Returning 0 instead '
             'of NaN for extent, area, and missing '
             'values.'.format(region=region, year=year, month=month))


def _create_validation_frame(dates, frame, hemisphere, eval_days, regression_delta_km2):
    """Return a dataframe slice with updated failed_qa columns selected over
    an evaluation date range based on the results of a linear regression analysis.

    Parameters:

    dates: pandas period Index
    frame: sedna dataframe
    hemisphere: the hemisphere to work with ('N', 'S')
    eval_days: number of evaluation days to utilize when evaulating data against the regression
    regression_delta_km2: Max difference between data and regression prediction
    """
    evaluation_dates = pd.period_range(dates[0]-eval_days, dates[-1])
    validation_frame = frame.xs(hemisphere, level='hemisphere')[['total_extent_km2',
                                                                 'failed_qa',
                                                                 'filename']]
    validation_frame = validation_frame.reindex(evaluation_dates)
    validation_frame = _set_failed_qa_flag(validation_frame, eval_days, regression_delta_km2)
    validation_frame = validation_frame.loc[dates]
    validation_frame['hemisphere'] = hemisphere
    validation_frame = validation_frame.set_index('hemisphere', append=True, drop=True)
    validation_frame = validation_frame.drop(['total_extent_km2', 'filename'], 1)
    return validation_frame


def _parse_period_from_date(date):
    return pd.Period(date, 'D')


def _parse_period_from_month(month):
    return pd.Period(month, 'M')


def _source_dataset(filename_list):
    """Return source dataset based on filenames in the filelist."""

    if filename_list == []:
        return None
    elif any(('_nrt_' in fn) for fn in filename_list):
        return 'nsidc-0081'
    else:
        return 'nsidc-0051'
