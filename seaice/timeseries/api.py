"""API definition for seaicetimeseries.

A package for accessing and manipulating sea ice timeseries data.

"""
import datetime as dt

import numpy as np
import pandas as pd

from . import access
from . import common as c
from . import warp
import seaice.nasateam as nt


def daily(hemisphere=None,
          start_date=None, end_date=None,
          data_store=nt.DAILY_DATA_STORE_FILENAME,
          columns=nt.DAILY_DEFAULT_COLUMNS,
          interpolate=-1, nday_average=0, min_valid=2,
          preserve_nan=False, filter_failed_qa=True):

    """Return a Pandas dataframe of the data in data_store filtered by input parameters.

    Keyword Arguments
    -----------------

    hemisphere: Select 'N' for northern or 'S' for southern to return only
         data for desired hemisphere.

    start_date: numpy datetime64 object whose value is the first day of
         data to return.  If 'None', return the first available date in the
         data_store.

    end_date: numpy datetime64 object whose value is the last day of data
         to return. If 'None', then return everything up until the last day of
         data in the data_store.

    data_store: 'sedna' style backend file. Where the data are in CSV format
         and columns are date, total_extent_km2, total_area_km2, missing_km2,
         hemisphere, filename.  The default value is this package's
         DAILY_DATA_STORE_FILENAME.

    columns: list of columns to extract and return from the datastore. By
         default this list contains nt.DAILY_DEFAULT_COLUMNS which are the data
         and metadata for the whole hemisphere.  If this list is empty [], return
         every column in the datastore.

    interpolate: number of missing NaN values to fill in a column.  Calls
         Pandas.Series.interpolate using default 'linear' interpolation.
         Interpolate will operate on all columns excluding NT.METADATA_COLUMNS and
         return a copy of the original dataframe with each column's values
         replaced with interpolated values.  This operation will also drop any
         missing data columns.

            - value <= 0 No interpolation. (default)

            - value > 0 Interpolate if only 'value' values are missing
              (suggest: 1).

            - None fill any missing regardless of number of consecutive
              missing (not recommended).

    nday_average: Number of days to use to compute a rolling mean.  This number
         is the width of the moving window, or the number of values used in
         calculating the statistic. ASINA and other projects will use a 5 day
         rolling mean in order to smooth data to have nicer looking graphs.

    min_valid: If nday_average is non-zero, this is the number of days of
         valid data required within the nday_average window in order to
         compute a valid mean for the window.

    preserve_nan : If nday_average is non-zero, and this flag is set to
        True, np.nan will be returned for any values that were originally missing,
        regardless of if an average could be calculated for them.

    filter_failed_qa: Set all returned values to np.nan for rows with failed_qa
                      set as true in the data store.  Defaults to True
    """
    df = access._dataframe_from_data_store(data_store)
    df = warp.collapse_hemisphere_index(df)
    df = warp.filter_hemisphere(df, hemisphere)
    df.index = df.index.to_timestamp()
    if filter_failed_qa:
        df = warp.filter_failed_qa(df)
    df = warp.filter_columns(df, columns)

    if interpolate is None or interpolate > 0:
        df = warp.interpolate_df(df, interpolate)
        df = warp.drop_missing_columns(df)

    if nday_average > 0:
        df = warp.nday_average(df, nday_average, min_valid, preserve_nan, False)

    df = warp.filter_before(df, start_date)
    df = warp.filter_after(df, end_date)

    return df


def monthly(hemisphere=None,
            start_date=None, end_date=None, month_num=None,
            data_store=nt.MONTHLY_DATA_STORE_FILENAME,
            columns=nt.MONTHLY_DEFAULT_COLUMNS):
    """Return a Pandas dataframe of the monthly data in data_store filtered by
    the input parameters

    Keyword Arguments
    -----------------

    hemisphere: Either 'N' for northern or 'S' for southern to return only
         data for selected hemisphere.

    start_date: Python datetime.date object whose value is the first day of
         data to return.  If not None, exclude date before this date from the
         returned dataframe.  Since the data_store data is monthly, consider
         any date within a month to be part of that month.  i.e. if the date
         is entered as a datetime.date(2000, 3, 15), no data would be included
         for Feb 2000 or earlier.

    end_date: Python datetime.date object whose value is the last day of data
         to return. If not None, then exclude any data after this date from
         the returned dataframe.

    month_num: Filter returned data to only this month.  i.e. if you only
         wanted to examine January data you would set this value to 1.

    data_store: 'sedna' style backend file. Where the data are in CSV format
         and columns are month, total_extent_km2, total_area_km2,
         missing_km2, hemisphere, filename.  The default value is this
         package's MONTHLY_DATA_STORE_FILENAME.

    columns: list of columns to extract and return from the datastore. By
         default this list contains nt.MONTHLY_DEFAULT_COLUMNS which are the data
         and metadata for the whole hemisphere.  If this list is empty [], return
         every column in the datastore.

    """
    df = access._dataframe_from_data_store_monthly(data_store)
    df = warp.collapse_hemisphere_index(df)
    df = warp.filter_hemisphere(df, hemisphere)
    df = warp.filter_columns(df, columns)
    df = warp.filter_before(df, start_date)
    df = warp.filter_after(df, end_date)
    if month_num is not None:
        df = df[df.index.month == month_num]

    return df


def monthly_rates_of_change(hemisphere, data_store=nt.DAILY_DATA_STORE_FILENAME):
    """Return a Pandas dataframe of the data in data_store for the specified
    hemisphere. Statistics related to monthly change are computed and included
    in the returned DataFrame.

    Keyword Arguments
    -----------------
    data_store: 'sedna' style backend file. Where the data are in CSV format and
        columns are date, total_extent_km2, total_area_km2, missing_km2,
        hemisphere, filename.  The default value is this package's
        DAILY_DATA_STORE_FILENAME.

    """
    df = daily(hemisphere, data_store=data_store)

    # don't include the current month in the rates of change calculation
    first_of_this_month = dt.date.today().replace(day=1).strftime('%Y-%m-%d')
    df = df[df.index < first_of_this_month]

    df['extent'] = scale(df.total_extent_km2)
    df = df[['extent', 'hemisphere']]

    df['interpolated_extent'] = df.extent.interpolate(limit=1)
    df['5 Day'] = nday_average(df['interpolated_extent'], num_days=5, min_valid=2)

    df['day'] = df.index.day
    df['month'] = df.index.month
    df['year'] = df.index.year

    a = df.groupby([df.index.year, df.index.month])
    mismatch = a['interpolated_extent'].count() == a['day'].last()

    a = df.groupby([df.index.year, df.index.month]).last()
    a['ice change Mkm^2 per month'] = a['5 Day'].diff(periods=1)

    # Set bad data
    a.loc[mismatch == False, ['5 Day', 'ice change Mkm^2 per month']] = None  # noqa

    a['ice change km^2 per day'] = (a['ice change Mkm^2 per month'] / a['day']) * 1000000
    a['ice change mi^2 per month'] = a['ice change Mkm^2 per month'] * c.KM2_TO_MI2 * 1000000
    a['ice change mi^2 per day'] = a['ice change km^2 per day'] * c.KM2_TO_MI2

    return a


def climatology_average_rates_of_change(hemisphere, data_store=nt.DAILY_DATA_STORE_FILENAME):
    """Return a Pandas dataframe of the data in data_store for the specified
    hemisphere. The average rate of change for each month over climatological
    range (1981-2010) is computed.

    Keyword Arguments
    -----------------
    data_store: 'sedna' style backend file. Where the data are in CSV format and
        columns are date, total_extent_km2, total_area_km2, missing_km2,
        hemisphere, filename.  The default value is this package's
        DAILY_DATA_STORE_FILENAME.

    """
    df = monthly_rates_of_change(hemisphere, data_store=data_store)

    # use a DatetimeIndex instead of a year/month MultiIndex
    df['date'] = df.apply(lambda x: pd.Timestamp(x.year, x.month, x.day), axis='columns')
    df = df.set_index(['date'], drop=True)

    df = warp.filter_before(df, pd.Timestamp(c.DEFAULT_CLIMATOLOGY_DATES[0]))
    df = warp.filter_after(df, pd.Timestamp(c.DEFAULT_CLIMATOLOGY_DATES[1]))

    df = df.set_index([df.index.year, df.index.month])

    climatology = df.groupby(df.month).mean()

    return climatology


def nday_average(series, num_days=c.NUM_DAYS, min_valid=c.MIN_VALID_DAYS):
    """Convenience function for computing nday averages on a dataframe column (Series)"""
    return series.rolling(window=num_days, min_periods=min_valid).mean()


def scale(series, divisor=1e6, precision=3):
    """Return a given series with its values divided and rounded.

    Keyword Arguments
    -----------------
    series: the data to scale

    divisor: the number by which the data should be divided, e.g., 1e6 to
        convert km^2 to millions of km^2 (default: 1e6)

    precision: the nummber of decimal places to preserve after dividing
        (default: 3)

    """
    return series.apply(lambda x: round(float(x) / divisor, precision))


def normal_statistics(series, clim_years=nt.DEFAULT_CLIMATOLOGY_YEARS, smooth_days=0):
    """Return mean and standard deviation statistics.

    Compute the mean and standard deviation of a daily timeseries for all of
    the years bounded within 'clim_years' inclusive.

    Data is grouped by Day of Year and then mean and standard deviations are
    computed across the group. Data on day of year (DOY) 366 is taken from a
    combination of December 31sts for leap years and Jan 1sts (of following
    years) for non-leap years. (Jan 1st will not be used following the last
    year of the climatology.)

    Returns a dataframe with columns named [series.name]_mean and
    [series.name]_std and indexed by 'day of year'

    """
    df = warp.mean_and_standard_deviation(series, clim_years)
    if smooth_days > 0:
        df = warp.nday_average(df, smooth_days, min_valid=1, preserve_nan=True, wrapped=True)
    return df


def quantiles(series, clim_years=nt.DEFAULT_CLIMATOLOGY_YEARS,
              levels=c.DEFAULT_QUANTILES, smooth_days=0):
    """Return quantile information.

    Quantile information is computed for each day of year (DOY) (0-366).

    Returns a multiindexed dataframe of quantile information from the input series.
    index is Day of Year, and columns are quantile values.

    A pandas multiindexed series for the desired quantile can be retrieved by
    using the .loc selector on the returned value.


    >>> series
    1979-02-28    16
    1979-03-01    15
    1980-02-28    13
    1980-02-29    14
    1980-03-01    15
    1981-02-28    15
    1981-03-01    16
    Name: test, dtype: float64


    >>> qs = quantiles(series, (1979, 1981), [0, .5, 1])
    >>> qs
             0.0  0.5  1.0
 day of year
        59  13   15   16
        60  14   15   16
        61  15   15   15

    """
    df = warp.quantiles(series, clim_years, levels)
    if smooth_days > 0:
        df = warp.nday_average(df, smooth_days, 1, False, True)
    return df


def monthly_anomaly(series, climatology_years):
    """Return the monthly anomaly for a monthly series over a set of years.

    It computes the mean of the climatology_years for each month, and then
    subtracts those climatology mean values from each value in the series
    based on that value's month.

    jan_value_1 - jan_mean_clim_years
    jan_value_2 - jan_mean_clim_years
    feb_value_1 - feb_mean_clim_years
    ....

    """
    s = series.copy()
    clim_means = warp.climatology_means(s, climatology_years)
    anomaly = s - clim_means[s.index.month].values
    return anomaly


def monthly_percent_anomaly(series, climatology_years):
    """Compute percent anomaly of a series.

    The maths were taken from the original idl code.
    It boils down to:

         100 * ((Series - Series_mean)  / Series_mean)

    """

    anomaly = monthly_anomaly(series, climatology_years)
    clim_means = warp.climatology_means(series, climatology_years)
    percent_anomaly = 100. * (anomaly / clim_means[anomaly.index.month].values)

    return percent_anomaly


def trend(series):
    """Compute the 1-degree best fit line for the given series, returned as a new
    series.

    """
    years = series.index.year

    x = years.copy()
    y = np.ma.masked_invalid(series)

    if y.mask.any():
        mask = y.mask
        x = x[~mask]
        y = y[~mask]

    polyfit = np.ma.polyfit(x, y, 1)
    trendline = np.polyval(polyfit, years)

    return pd.Series(trendline, index=series.index)


def climatology_means(series, climatology_years):
    """Given a series of monthly data (for one or more month values) gather each
    month's data (Jan, Feb, etc) that falls within the range
    climatology_years and compute the mean of those items.

    Arguments
    -------

    series: timeseries data (daily or monthly), that have a DatetimeIndex or
    PeriodIndex.

    climatology_years: a tuple bounding the years of interest.

    """
    return warp.climatology_means(series, climatology_years)
