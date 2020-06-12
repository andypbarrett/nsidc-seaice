""" Functions for locating Goddard nasateam files on a filesystem.
"""

import datetime as dt
import fnmatch
import os
from calendar import monthrange
from functools import lru_cache

import pandas as pd

from .errors import SeaIceDataInvalidSearchPathsError
import seaice.nasateam as nt
from .cache import SeaiceFsCache


def daily_file_path(hemisphere, period_index, search_paths):
    """Return a list of the names of files which contain data for the given
    hemisphere on the dates contained within the period_index.

    """
    return _daily_file_paths_in_period_index(hemisphere, period_index, search_paths)


def monthly_file_path(hemisphere, year, month, search_paths):
    """Return a list of filepaths for monthly data.
    """

    files = _find_all_nasateam_ice_files_multiple_paths(search_paths)

    data_frame = _get_monthly_filename_data_frame(files, hemisphere['short_name'])
    data_frame = data_frame[data_frame.index == '{y:04}-{m:02}'.format(y=year, m=month)]
    data_frame = _filter_by_preferred_platform_dates(data_frame)

    paths = list(data_frame.filename)

    if paths:
        return paths[0]
    else:
        return None


def all_daily_file_paths_for_month(hemisphere, year, month, search_paths):
    """Return a list of all the filenames available for the given year and month.
    """
    start_date = dt.date(year, month, 1)
    end_date = dt.date(year, month, monthrange(year, month)[1])

    return daily_file_paths_in_date_range(hemisphere, start_date, end_date, search_paths)


@SeaiceFsCache
def _find_all_nasateam_ice_files(directory, filter_='*nt_*.bin'):
    filelist = []
    for root, dirs, files in os.walk(directory):
        filelist.extend([os.path.join(root, f) for f in fnmatch.filter(files, filter_)])
    return sorted(filelist)


def _find_all_nasateam_ice_files_multiple_paths(search_paths):
    if isinstance(search_paths, str):
        raise SeaIceDataInvalidSearchPathsError('search_paths must be an iterable other than str')

    ice_files = []
    for sp in search_paths:
        ice_files.extend(_find_all_nasateam_ice_files(sp))
    return tuple(sorted(ice_files))


def _filter_overlapping_nrt_and_final(file_list=[]):
    """Return one file name per date. Up to the date
    nt.LAST_DAY_WITH_VALID_FINAL_DATA, prefer gsfc-final files over near
    real-time files.

    Keyword Arguments:
    file_list -- list of file names (default [])

    """
    @lru_cache(maxsize=None)
    def _date_from_filename(filename):
        datestr = nt.DATA_FILENAME_MATCHER.search(filename).group('date')
        return dt.datetime.strptime(datestr, '%Y%m%d').date()

    # nrt files are clearly identified
    nrt_file_list = [f for f in file_list
                     if nt.DATA_FILENAME_MATCHER.search(f).group('version') == 'nrt']

    # final files are all the rest
    final_file_list = list(set(file_list) - set(nrt_file_list))

    # we only want final files for dates up to LAST_DAY_WITH_VALID_FINAL_DATA
    final_file_list = [f for f in final_file_list
                       if _date_from_filename(f) <= nt.LAST_DAY_WITH_VALID_FINAL_DATA]

    # keep only nrt files for dates where we don't have a final file
    final_dates = [_date_from_filename(f) for f in final_file_list]
    nrt_file_list = [f for f in nrt_file_list if _date_from_filename(f) not in final_dates]

    return sorted(final_file_list + nrt_file_list)


@lru_cache(maxsize=2)
def _get_daily_filename_data_frame(file_list, hemi_short_name):
    filename_matches = [nt.DATA_FILENAME_MATCHER.search(f) for f in file_list]
    parsed_daily_filenames = [m.groups() for m in filename_matches if m.group('day')]

    df = pd.DataFrame().from_records(
        parsed_daily_filenames,
        columns=['filename', 'date', 'year', 'month', 'day', 'platform', 'version', 'hemisphere']
    )

    # the data files have 'n' or 's' for the hemisphere indicator, but we prefer
    # to work with capital letters for the hemispheres
    df.hemisphere = df.hemisphere.apply(str.upper)

    df = df.set_index(pd.to_datetime(df['date'].values).to_period('D'))

    df = df[df.hemisphere == hemi_short_name]

    return df


@lru_cache(maxsize=2)
def _get_monthly_filename_data_frame(file_list, hemi_short_name):
    """"Returns a Pandas DataFrame constructed from the given list of filenames,
    filtered by hemisphere. The DataFrame is indexed by Period and is useful for
    extracting files matching certain kinds of date ranges, e.g., a given month
    across a range of years. To create an indexed DataFrame for monthly files, a
    day-of-month value of 1 is used (e.g., January 1980 is indexed as January 1,
    1980).
    """
    filename_matches = [nt.DATA_FILENAME_MATCHER.search(f) for f in file_list]
    parsed_monthly_filenames = [m.groups() for m in filename_matches if not m.group('day')]

    df = pd.DataFrame().from_records(
        parsed_monthly_filenames,
        columns=['filename', 'date', 'year', 'month', 'day', 'platform', 'version', 'hemisphere']
    )

    # the data files have 'n' or 's' for the hemisphere indicator, but we prefer
    # to work with capital letters for the hemispheres
    df.hemisphere = df.hemisphere.apply(str.upper)

    df = df.drop('day', axis=1)

    df = df.set_index(pd.to_datetime(df['date'].values + '01').to_period('M'))

    df = df[df.hemisphere == hemi_short_name]

    return df


def _filter_by_preferred_platform_dates(data_frame):
    """Return a new DataFrame with exactly one row per hemisphere per date,
    selecting the file associated with the preferred platform when necessary.
    """

    def preferred_platform(row):
        platform = row['platform']
        if platform not in nt.PLATFORM_RANGES:
            return False

        for start, finish in nt.PLATFORM_RANGES[platform]:
            # row.name is really the index of that row, which is a pd.Period
            row_period = row.name

            # choose the 15th of the month to match the old IDL code
            #
            # this means if there are multiple files (different platforms) for
            # that month, the preferred platform is the one used on the 15th
            if row_period.freqstr == 'M':
                row_period = pd.Period(dt.date(row_period.year, row_period.month, 15), 'D')

            if pd.Timestamp(start) <= row_period.to_timestamp() <= pd.Timestamp(finish):
                return True

        return False

    def filter_platform(df):

        try:
            df = df[df.apply(preferred_platform, axis=1)]
        except ValueError:  # DataFrame.__getitem__: 'Must pass DataFrame with boolean values only'
            # either nothing was bad, or nothing in the bad set passed the filter
            pass

        return df

    north = data_frame[data_frame.hemisphere == nt.NORTH['short_name']]
    south = data_frame[data_frame.hemisphere == nt.SOUTH['short_name']]

    north = filter_platform(north)
    south = filter_platform(south)

    data_frame = north.append(south).sort_index()

    return data_frame


def daily_file_paths_in_date_range(hemisphere, start_date, end_date, search_paths):
    """Return a list of filenames containing data for the given hemisphere within
    the inclusive range defined by the given start and end dates.

    """
    period_index = pd.period_range(start_date, end_date, freq='D')
    return _daily_file_paths_in_period_index(hemisphere, period_index, search_paths)


def _daily_file_paths_in_period_index(hemisphere, period_index, search_paths):
    """Return a list of filenames containing data for the given hemisphere on dates
    contained within the given period_index.

    """
    files = _find_all_nasateam_ice_files_multiple_paths(search_paths)

    data_frame = _get_daily_filename_data_frame(files, hemisphere['short_name'])

    labels = data_frame.index.intersection(period_index)
    if labels.empty:
        return []
    data_frame = data_frame.loc[labels]

    data_frame = _filter_by_preferred_platform_dates(data_frame)

    paths = list(data_frame.filename)

    paths = _filter_overlapping_nrt_and_final(paths)

    return paths
