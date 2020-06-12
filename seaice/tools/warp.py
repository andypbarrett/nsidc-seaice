"""Pure functions for manipulating Pandas DataFrames.

"""
import logging

import numpy as np
import pandas as pd
from scipy.stats import linregress

import seaice.nasateam as nt
import seaice.timeseries as sit

log = logging.getLogger('sea-ice-tools')

MISSING = '-9999'


def add_extent_climatology(df_in, mean):
    data = df_in.copy()
    data['extent-anomaly'] = data.extent - mean
    return data


def add_rank(df_in):
    df = df_in.copy()

    df['rank'] = pd.DataFrame(data=df['extent'].rank(ascending=1))

    return df


def add_trends(df_in, mean):
    """For each year, accumulate extent trend values through the year."""
    data = df_in.copy()
    data = _initialize_trend_columns(data)

    for i in range(0, len(data)):
        cum_df = data.iloc[:i+1][['year', 'extent']].dropna(axis=0)

        # Ignore invalid value warnings from numpy when running linregress.
        # It will complain if the number of observations is < 3.
        old_settings = np.seterr(invalid='ignore')
        (slope, intercept, r_value, p_value, stderr) = linregress(cum_df['year'], cum_df['extent'])
        np.seterr(**old_settings)

        data.ix[i, ['trend-through-year-km^2-per-year']] = round(slope, 4) * 1000000
        data.ix[i, ['r-value', 'p-value', 'stderr']] = r_value, p_value, stderr
        data.ix[i, '%-trend-through-year'] = slope / mean * 10 * 100.
        data.ix[i, 'significant'] = np.int((np.square(r_value) >= .65) & (p_value <= .05))

    # Mark all missing data as missing, but keep the year and month columns
    data[pd.isnull(data.extent)] = None
    data.year = data.index.year
    data.month = data.index.month

    return data


def change_filepath_to_ftp(df_in):
    """Return a new copy of the given dataframe where values in the filename column
    have been changed from /projects/DATASETS to a publicly-accessible FTP link.

    """
    df = df_in.copy()

    df.filename = df.filename.apply(
        lambda x: x.replace('/projects', 'ftp://sidads.colorado.edu/pub')
    )

    return df


def change_filepaths_to_ftp(df_in):
    """Return a new copy of the given dataframe where values in the filename column
    have been changed from /projects/DATASETS to a publicly-accessible FTP link.

    """
    df = df_in.copy()

    df.filename = df.filename.apply(
        lambda x: [fn.replace('/projects', 'ftp://sidads.colorado.edu/pub') for fn in x]
    )

    return df


def climatology_mean_extent(df_in):
    data = df_in.copy()
    climatological_mean = data[(data.index.year >= nt.DEFAULT_CLIMATOLOGY_YEARS[0]) &
                               (data.index.year <= nt.DEFAULT_CLIMATOLOGY_YEARS[1])].extent.mean()
    return climatological_mean


def column_to_width(df_in, column, width):
    """Pad the column header and the values in the column with whitespace to a
    specific width.

    """
    df = df_in.copy()

    df[column] = df[column].apply(lambda x: ('{:>' + str(width) + '}').format(x))
    df = df.rename(columns={column: ('{:>' + str(width) + '}').format(column)})

    return df


def columns_to_width(df_in, column_width_dict):
    df = df_in.copy()

    for column, width in column_width_dict.items():
        df = column_to_width(df, column, width)

    return df


def drop_rows_with_cond(df_in, column, fn=lambda x: False):
    """Drop rows where the given condition fn returns True for values in the given
    column.

    """
    df = df_in.copy()

    df = df[~df[column].apply(fn)]

    difference = df_in.index.difference(df.index)
    if len(difference) > 0:
        log.debug('warp.drop_rows_with_cond: dropped rows in index {}'.format(difference))

    return df


def float_columns_to_string(df_in, columns, precision):
    """Convert values in listed columns from float/numpy.float64 to a string
       representation.  All non-float values in the column will be ignored.
       Returns updated copy of dataframe

       Arguments:

       - df_in:      Dataframe to evaluate
       - precision:  Number of decimal places to display
       - columns:    Columns to convert
    """

    df = df_in.copy()
    for column in columns:
        df[column] = df[column].apply(_format_float_value, args=(precision,))
    return df


def _format_float_value(val, precision):
    if type(val) in (float, np.float64):
        return '{:.{}f}'.format(val, precision)
    return val


def modified_extents(df_in):
    """Return a dataframe with columns for interpolated extent and 5 day trailing
    average of the interpolated extent, in units of millions of km^2.

    The following columns are required for df_in:
        - total_extent_km2
        - hemisphere

    """
    df = df_in.copy()

    df['interpolated_extent'] = df['total_extent_km2'].interpolate(limit=1)
    df['5-day'] = sit.nday_average(df['interpolated_extent'], num_days=5, min_valid=2)

    # scale from km^2 to millions of km^2
    df['extent'] = sit.scale(df['total_extent_km2'])
    df['interpolated_extent'] = sit.scale(df['interpolated_extent'])
    df['5-day'] = sit.scale(df['5-day'])

    df = df[['extent', 'hemisphere', 'interpolated_extent', '5-day']]

    return df


def order_by_rank(df_in):
    data = df_in.copy()
    ordered = pd.DataFrame(index=data.index)
    ordered[' reordered => '] = ' '
    ordered['ordered-rank'] = pd.DataFrame(data=data['extent'].rank(ascending=1))
    ordered['ranked-year'] = data['year']
    ordered['ranked-extent'] = data['extent']
    ordered = ordered.sort_values('ordered-rank', ascending=True)
    return ordered


def rename_and_scale(df_in, columns={}, divisor=1e6, precision=3):
    df = df_in.copy()

    df = df.rename(columns=columns)
    for col in columns.values():
        df[col] = sit.scale(df[col], divisor=divisor, precision=precision)

    return df


def replace_nan(df_in, columns=[], value=np.nan):
    df = df_in.copy()

    for col in columns:
        df[col] = df[col].apply(lambda x: value if np.isnan(x) else x)

    return df


def restrict_filename(df_in):
    df = df_in.copy()

    for index, row in df.iterrows():
        date = index.date()
        yyyymmdd = date.strftime('%Y%m%d')

        dates = [nt.DATA_FILENAME_MATCHER.search(f).group('date') for f in row.filename]

        try:
            file_index = dates.index(yyyymmdd)
            file_ = row.filename[file_index]
        except ValueError:
            file_ = ''
            log.debug('warp.restrict_filename: no filename found matching {}'.format(
                date.isoformat()))

        df.at[index, 'filename'] = file_

    return df


def seaicetimeseries_df_to_extent_csv_df(df_in, divisor=1e6, precision=3, missing=np.nan):
    df = df_in.copy()
    df['day'] = df.index.day
    df['month'] = df.index.month
    df['year'] = df.index.year

    columns = {'total_extent_km2': 'extent',
               'total_area_km2': 'area',
               'missing_km2': 'missing'}
    df = rename_and_scale(df, columns, divisor, precision)
    df = replace_nan(df, columns.values(), missing)

    df = drop_rows_with_cond(df, 'filename', lambda x: len(x) == 0)

    return df


def seaicetimeseries_df_to_monthly_sea_ice_index_df(df_in, precision=2):
    df = df_in.copy()

    df['month'] = df.index.month
    df['year'] = df.index.year

    columns = {'total_extent_km2': 'extent',
               'total_area_km2': 'area'}
    df = rename_and_scale(df, columns, divisor=1e6, precision=precision)

    df['data-type'] = df['source_dataset'].apply(source_to_data_type, args=(MISSING,))

    df = df[['year', 'month', 'data-type', 'hemisphere', 'extent', 'area']]

    return df


def source_to_data_type(source, missing):
    try:
        map_ = {'nsidc-0051': 'Goddard', 'nsidc-0081': 'NRTSI-G'}
        return map_.get(source, missing)

    except TypeError:
        return missing


def seaicetimeseries_df_to_monthly_csv_df(df_in, divisor=1e6, precision=2, missing=MISSING):
    df = df_in.copy()

    df['month'] = df.index.month
    df['year'] = df.index.year

    columns = {'total_extent_km2': 'extent',
               'total_area_km2': 'area',
               'missing_km2': 'missing'}
    df = rename_and_scale(df, columns, divisor, precision)
    df = replace_nan(df, columns.values(), missing)

    df = df.rename(columns={'month': 'mo',
                            'source_dataset': 'data-type'})

    df['data-type'] = df['data-type'].apply(source_to_data_type, args=(missing,))

    return df


def split_by_column(df_in, column, values=[]):
    df = df_in.copy()

    return [df[df[column] == value] for value in values]


def _initialize_trend_columns(df_in):
    data = df_in.copy()
    columns = ['trend-through-year-km^2-per-year',
               'p-value',
               'r-value',
               'stderr',
               'significant',
               '%-trend-through-year']
    for c in columns:
        data[c] = None
        data[c] = data[c].astype(np.float64)

    return data
