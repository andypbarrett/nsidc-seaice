"""Routines for manipulating a Pandas dataframe.

These are a collection of useful tools for mainpulating data series as
represented by a Pandas dataframe.

"""

import datetime as dt
import re
from functools import partial

import pandas as pd
import numpy as np

from .common import SeaIceTimeseriesInvalidArgument
from .common import DEFAULT_QUANTILES
import seaice.nasateam as nt


def filter_failed_qa(df):
    """Return frame with np.nan set for all rows that have failed_qa set to true"""
    df = df.copy()
    if 'failed_qa' in df.columns:
        df['failed_qa'] = df['failed_qa'].replace(np.nan, False)
        df['failed_qa'] = df['failed_qa'].astype('bool')
        df.loc[df.failed_qa, (df.columns.difference(['failed_qa', 'filename']))] = np.nan
        df.loc[df.failed_qa, ['filename']] = ''
    return df


def collapse_hemisphere_index(df):
    """Returns frame with 'hemisphere' index level removed from index and added
       as a data column"""
    updated_frame = df.copy()
    return updated_frame.reset_index(level='hemisphere', drop=False)


def filter_hemisphere(df, hemisphere):
    """Return data frame filtering all rows where hemisphere not equal to input value."""

    if hemisphere in nt.VALID_HEMISPHERES:
        return df[df['hemisphere'] == hemisphere]
    raise SeaIceTimeseriesInvalidArgument('Must provide a valid hemisphere for filtering')


def filter_before(df, date_):
    """Return df excluding rows where index dates are before input date_"""
    try:
        return df[df.index >= date_]
    except (AttributeError, TypeError):
        return df


def filter_after(df, date_):
    """Return df excluding rows where index dates after input date_"""
    try:
        return df[df.index <= date_]
    except (AttributeError, TypeError):
        return df


def filter_columns(df_in, columns=[]):
    """Return a subset of columns from the input DataFrame"""
    df = df_in.copy()
    if columns:
        df = df_in[columns]
    return df


def interpolate_df(df_in, limit, columns=[]):
    """Interpolate the data columns in the input dataframe

    Arguments:
    --------

    df_in:  input dataframe to interpolate

    limit: number of nan values to interpolate across.

    columns: a list of columns to interpolate.  If empty then every column
             but nt.METADATA_COLUMNS are interpolated. [Those are columns
             with metadata like 'hemisphere', 'filename', and
             'source_dataset']

    """

    if not columns:
        columns = list(set(df_in.columns) - set(nt.METADATA_COLUMNS))
        columns.sort()

    df = pd.DataFrame()
    for col in columns:
        df[col] = df_in[col].interpolate(limit=limit)

    return df


def _series_name(date_index):
    start = date_index[0].year
    end = date_index[-1].year

    if start == end:
        return str(start)
    else:
        return '{start}-{end}'.format(start=start, end=end)


def _stacked_clim(series, clim_years):
    """Return a stacked climatology

    Arguments
    -------

    series : input daily series with a DateTimeIndex.

    clim_years: (begin, end) tuple of years to use to compute statistics.

    The input series is reordered into 366 day of year(rows) by
    clim_years(columns) and returned as a Dataframe
    """
    start_date = dt.date(clim_years[0], 1, 1)
    periods = 366
    list_of_clim_years = list(np.arange(clim_years[0], clim_years[1]+1))
    stacked_clim = _reorder_daily_series_by_years(series, start_date, periods=periods,
                                                  years=list_of_clim_years)
    stacked_clim.index = stacked_clim.index + 1
    stacked_clim.index.name = 'day of year'
    return stacked_clim


def _reorder_daily_series_by_years(series, start, end=None, periods=None, years=[]):

    """Gather timeseries data into "aligned" years.


    series: Daily series with datetime index with period of
            1-Day

    start : string or datetime-like, left bound for generating dates

    end: string or datetime-like, right bound for generating dates

    periods: number of days of data to select.

    years: years to align series subsets. defaults to the left bounds's year

    This function is used to "align" days beyond a starting epoch across
    different years.  The index is a zero based index representing the number
    of days past the left-bounds.  So the 0th index value is the start date,
    1st value is one day beyond that.

    """

    default_index = pd.date_range(start=start, end=end, periods=periods, freq='D')
    periods = len(default_index)
    stacked_array = pd.DataFrame(index=np.arange(len(default_index)))
    stacked_array.index.name = default_index[0].to_pydatetime().strftime('%Y-%m-%d')

    if not years:
        years = [default_index[0].year]

    for year in years:
        shift_years = year - default_index[0].year
        shift_start = default_index[0] + pd.DateOffset(years=shift_years)
        shift_index = pd.date_range(start=shift_start, periods=periods, freq='D')
        shift_array = series.reindex(index=shift_index)
        shift_array.name = _series_name(shift_index)
        stacked_array = pd.concat([stacked_array, shift_array.reset_index(drop=True)],
                                  axis=1, sort=True)

    return stacked_array


def nday_average(df_in, nday_average, min_valid, preserve_nan, wrapped):

    """Return the rolling mean of a seaicetimeseries data/stats  dataframe.

    Returns a copy of the input dataframe with each data column replaced with
    its rolling mean (n-day average), optionally with all original missing values
    preserved as np.nan if the preserve_nan flag is set, optionally rolling the
    final nday_average number of days into the front of the dataframe if the wrapped
    flag is set.
    """
    df = df_in.copy()
    for col in set(df.columns) - set(nt.METADATA_COLUMNS):
        df[col] = _series_nday_average(df[col], nday_average, min_valid, preserve_nan, wrapped)
    return df


def _series_nday_average(series, nday_average, min_valid, preserve_nan, wrapped):
    series = series.copy()
    update_series = series.copy()

    if wrapped:
        # Convert to integer index to allow for any type of dataframe
        update_series = update_series.reset_index(drop=True)

        tail_col = update_series[-nday_average:]
        tail_col = pd.Series(tail_col.data, list(range(-nday_average, 0)))
        update_series = tail_col.append(update_series)

        # Deselect 'wrapped' values, reset index to original values
        update_series = (update_series.rolling(window=nday_average,
                                               min_periods=min_valid).mean())
        update_series = update_series.loc[0:]
        update_series.index = series.index
    else:
        update_series = (update_series.rolling(window=nday_average,
                                               min_periods=min_valid).mean())
    if preserve_nan:
        update_series.loc[series.isnull()] = np.nan

    return update_series


def mean_and_standard_deviation(series, clim_years):
    """Return climatological means and standard deviations by Day of Year for a
    series daily numeric data with a datetime index.

    Each climatology value is selected based on the day of year (DOY)
    starting on January 1st. This means that data for DOY 366 is taken from a
    combination of December 31st for leap years and following Jan 1st for
    non-leap years.

    Arguments
    ----------
    series : input daily series with a DateTimeIndex.

    clim_years: (begin, end) tuple of years to use to compute statistics.

    returns: A new dataframe indexed by day of year [1-366]
    for ['NAME'_mean, 'NAME'_std]. If the input series has name
    'total_extent_km2', the output dataframe will have
    'total_extent_km2_mean', 'total_extent_km2_std'.

    """
    stacked_clim = _stacked_clim(series, clim_years)

    mean = stacked_clim.mean(axis=1)
    mean.name = '{0}_mean'.format(series.name)

    std = stacked_clim.std(axis=1)
    std.name = '{0}_std'.format(series.name)

    ret = pd.concat([mean, std], axis=1, sort=True)
    return ret


def quantiles(series, clim_years, levels=DEFAULT_QUANTILES):
    """Return Day of Year quantile values.

    Arguments
    ---------

    series : input daily series with a DateTimeIndex.

    clim_years:  tuple of bounding years (inclusive) to select data from.

    levels: list of quantile values [0, 1] to compute.

    Returns a dataframe of quantile information from the input series.
    index is Day of year, and columns are quantile values.

    """
    # only interesting years
    stacked_clim = _stacked_clim(series, clim_years)

    df = pd.DataFrame(index=stacked_clim.index)

    for level in levels:
        df[level] = stacked_clim.apply(partial(np.nanpercentile, q=level * 100), axis=1)

    df = df.dropna()

    return df


def drop_missing_columns(df_in):
    """ Drop any columns with missing in it name. """
    df = df_in.copy()
    [df.drop(c, axis=1, inplace=True) for c in df.columns if re.search('missing', c)]
    return df


def climatology_means(series, climatology_years):
    """Given a series of monthly data (for one or more month values) gather each
    month's data (Jan, Feb, etc) that falls within the range
    climatology_years and compute the mean of those items.

    Return a series of (month, mean values)

    """
    s = series.copy()
    clim_year_series = s[(s.index.year >= climatology_years[0]) &
                         (s.index.year <= climatology_years[1])]

    climatology_means_by_month = clim_year_series.groupby(clim_year_series.index.month).mean()

    return climatology_means_by_month
