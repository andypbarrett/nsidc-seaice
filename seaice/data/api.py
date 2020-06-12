from statistics import mode
import copy
import datetime as dt
import functools

import numpy as np
import pandas as pd
import scipy.stats

from . import gridset_filters as gf
from . import getter
from . import grid_filters
from . import trend
import seaice.nasateam as nt


def concentration_daily(hemisphere=None, year=None, month=None, day=None,
                        search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                        interpolation_radius=0, allow_empty_gridset=True,
                        allow_bad_dates=True, drop_land=False, drop_invalid_ice=False):
    """Return a gridset containing the sea ice concentration data and metadata.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy masked array for the daily
    concentration.

    'metadata' contains another dictionary with a key 'files' that is a list
    of source files that went into creating the data grid.

    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    year                 -- Integer year (4 digits)

    month                -- Integer month number.

    day                  -- Integer day number.

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    interpolation_radius -- If non-zero, search this many days before and
                            after the target date for files to use
                            to interpolate any missing data in the target
                            file.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception
                            rather than returning an empty_gridset() when no
                            data is available for the request.  Defaults to
                            'True'

    allow_bad_dates      -- If 'False', returns an empty gridset for days found
                            in the bad dates list. If 'True', the gridset with
                            bad data is returned.

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to False.

    """
    date = dt.date(year, month, day)

    gridset = getter.concentration_daily(hemisphere, date, search_paths, interpolation_radius)

    filters = _filters(hemisphere=hemisphere,
                       month=date.month,
                       drop_land=drop_land,
                       allow_bad_dates=allow_bad_dates,
                       interpolation_radius=interpolation_radius,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def concentration_daily_average_over_date_range(hemi,
                                                date_range,
                                                search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                                                allow_empty_gridset=True,
                                                drop_land=False,
                                                drop_invalid_ice=True):
    """Return a gridset containing the averaged concentration of a given set of
    days.

    hemi                 -- 'N' or 'S'

    date_range           -- pandas.DatetimeIndex(freq='D') containing a
                            continuous range of days to average

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception
                            rather than returning an empty_gridset() when no
                            data is available for the request.  Defaults to
                            True.

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to True.

    """
    nt_hemi = nt.by_name(hemi)

    gridset = getter.concentration_daily_average_over_date_range(nt_hemi,
                                                                 date_range,
                                                                 search_paths)

    [month], _ = scipy.stats.mode(date_range.month)

    filters = _filters(hemisphere=nt_hemi,
                       month=month,
                       drop_land=drop_land,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def extent_daily(hemisphere=None, year=None, month=None, day=None,
                 search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                 interpolation_radius=0, extent_threshold=nt.EXTENT_THRESHOLD,
                 allow_empty_gridset=True, allow_bad_dates=True,
                 drop_land=False, drop_invalid_ice=True):
    """Return a gridset containing the sea ice extent grid and metadata.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy masked array for the daily
    extent.

    'metadata' contains another dictionary with a key 'files' that is a list
    of source files that went into creating the data grid.

    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    year                 -- Integer year (4 digits)

    month                -- Integer month number.

    day                  -- Integer day number.

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    interpolation_radius -- If non-zero, search this many days before and
                            after the target date for files to use
                            to interpolate any missing data in the target
                            file.

    extent_threshold     -- The minimum concentration value that should be
                            counted as extent.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception rather than
                            returning an empty_gridset() when no data is available
                            for the request.  Defaults to 'True'

    allow_bad_dates      -- If 'False', returns an empty gridset for days found
                            in the bad dates list. If 'True', the gridset with
                            bad data is returned.

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to True.

    """

    date = dt.date(year, month, day)

    gridset = getter.concentration_daily(hemisphere, date, search_paths, interpolation_radius)

    filters = _filters(hemisphere=hemisphere,
                       month=date.month,
                       drop_land=drop_land,
                       allow_bad_dates=allow_bad_dates,
                       interpolation_radius=interpolation_radius,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset,
                       extent_threshold=extent_threshold)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def extent_daily_median(hemisphere=None, start_year=None, end_year=None, date=None,
                        dayofyear=None, search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                        interpolation_radius=1, extent_threshold=nt.EXTENT_THRESHOLD,
                        allow_empty_gridset=True, allow_bad_dates=False,
                        drop_land=False, drop_invalid_ice=False):
    """Returns a gridset containing a single grid representing the median sea ice
    extent for the selected dayofyear over the range of selected years. To
    calculate the median extent, gridcells that have ice at least 50% of the
    time are considered to be ice on the median grid.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    'metadata' contains another dictionary with keys 'files', 'years', and
    'dayofyear'

    metadata dictionary contents:

    'files' - Contains a list of filelists sorted by year. 'files[0]' is the
    list of files used to create the data for 'years[0]'

    'dayofyear' - The day of year you asked for. If a date object is passed in,
    the day of year will be calculated from it.

    'years' - List of years from the start_year to end_year.


    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    start_year           -- Integer year (4 digits)

    end_year             -- Integer year (4 digits)

    dayofyear            -- Integer day of year number.

    date                 -- datetime.date object to use as a reference date; its
                            day of year will be used if dayofyear is not
                            provided

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice extent files.

    interpolation_radius -- If non-zero, search this many days before and after
                            the target date for files to use to interpolate any
                            missing data in the target file. Because SMMR data
                            on the N07 platform (through Aug 1987) is available
                            only every other day we set the default value to 1
                            for this routine. This ensures that every year has
                            a valid ice grid to use in the median computation.
                            For the days of year that do not have a SMMR data
                            file a grid is created from averaging the previous
                            and following days.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception rather
                            than returning an empty_gridset() when no data is
                            available for the request.  Defaults to 'True'

    allow_bad_dates      -- If 'False', data from days in the bad dates list
                            will not be used; instead, an empty gridset will be
                            used when calculating the median.

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to False.

    """
    if (date is not None) and (dayofyear is None):
        dayofyear = date.timetuple().tm_yday

    gridset = getter.extent_daily_median(hemisphere, start_year, end_year,
                                         dayofyear, search_paths,
                                         interpolation_radius, extent_threshold,
                                         allow_bad_dates)

    filters = _filters(hemisphere=hemisphere,
                       start_year=start_year,
                       end_year=end_year,
                       dayofyear=dayofyear,
                       drop_land=drop_land,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def concentration_monthly(hemisphere=None, year=None, month=None,
                          search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                          allow_empty_gridset=True, drop_land=False,
                          drop_invalid_ice=False, ensure_full_nrt_month=False,
                          min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing monthly sea ice concentration data and metadata.

    Monthly data is returned from a single monthly data file after checking
    its validity. When a monthly file does not exist, the daily files are
    averaged to create the monthly concentration.  Final daily files are used
    when available, otherwise near real time daily files are used.

    When a month within the satellite era does not have enough valid data to
    be considered complete (e.g. Jan 1988), an empty data grid is
    returned. For requests before the satellite era or for the current or
    future months, an out of range error is raised.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy masked array for the monthly
    concentration.

    'metadata' contains another dictionary with a key 'files' that is a list
    of source files that went into creating the data grid.

    Keyword Arguments:
    ----------------
    hemisphere            -- nt.NORTH or nt.SOUTH

    year                  -- Integer year (4 digits)

    month                 -- Integer month number.

    search_paths          -- List of directories that will be recursively searched for
                             nasateam sea ice concentration files.

    allow_empty_gridset   -- If 'False', raise a SeaIceDataNoData exception rather
                             than returning an empty_gridset() when no data is
                             available for the request.  Defaults to 'True'

    ensure_full_nrt_month -- If 'True', raise a Exception rather than returning a
                             gridset that was created using a month with NRT data
                             and missing days

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.

    """

    if (year, month, hemisphere) in nt.BAD_CONCENTRATION_MONTHS:
        gridset = getter.empty_gridset(hemisphere['shape'], 'M')

    else:
        gridset = getter.concentration_monthly(hemisphere,
                                               year,
                                               month,
                                               search_paths,
                                               min_days_for_valid_month)

    filters = _filters(hemisphere=hemisphere,
                       month=month,
                       drop_land=drop_land,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset,
                       ensure_full_nrt_month=ensure_full_nrt_month)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def concentration_monthly_anomaly(hemisphere=None, year=None, month=None,
                                  start_year=None, end_year=None,
                                  search_paths=nt.DEFAULT_SEA_ICE_PATHS, allow_empty_gridset=True,
                                  ensure_full_nrt_month=False,
                                  min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing the difference between the concentration in the
    given year & month and the mean concentration for that month over the
    climatological period defined by start_year and end_year.

    Monthly data is returned from a single monthly data file after checking its
    validity. When a monthly file does not exist, the daily files are averaged
    to create the monthly concentration. Final daily files are used when
    available, otherwise near real time daily files are used.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy array for the anomaly.

    'metadata' contains another dictionary with various information about the
    grid, including the files used to create it.

    Keyword Arguments:
    ----------------
    hemisphere            -- nt.NORTH or nt.SOUTH

    year                  -- Integer year (4 digits)

    month                 -- Integer month number

    start_year            -- Integer year (4 digits); the start of the
                             climatology period

    end_year              -- Integer year (4 digits); the end of the climatology
                             period

    search_paths          -- List of directories that will be recursively searched for
                             nasateam sea ice concentration files

    allow_empty_gridset   -- If 'False', raise a SeaIceDataNoData exception rather
                             than returning an empty_gridset() when no data is
                             available for the request.  Defaults to 'True'

    ensure_full_nrt_month -- If 'True', raise a Exception rather than returning a
                             gridset that was created using a month with NRT data
                             and missing days

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.
    """
    filters = _filters(hemisphere=hemisphere, month=month, drop_invalid_ice=True,
                       allow_empty_gridset=allow_empty_gridset,
                       ensure_full_nrt_month=ensure_full_nrt_month)
    cutoff = functools.partial(gf.concentration_cutoff, nt.EXTENT_THRESHOLD)

    month_gridset = getter.concentration_monthly(hemisphere, year, month, search_paths,
                                                 min_days_for_valid_month)
    month_gridset = gf.apply_filters(month_gridset, filters + [cutoff])

    climatology_gridset = getter.concentration_monthly_over_years(hemisphere,
                                                                  start_year,
                                                                  end_year,
                                                                  month,
                                                                  search_paths,
                                                                  min_days_for_valid_month)
    climatology_gridset = gf.apply_filters(climatology_gridset,
                                           filters + [gf.apply_largest_pole_hole])

    gridset = _anomaly_gridset(month_gridset, climatology_gridset)

    return gridset


def concentration_monthly_trend(hemisphere=None, year=None, month=None,
                                search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                                min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
                                trend_start_year=None, *, clipping_threshold):
    """Return a gridset containing the trend of concentration for the given month in
    percentage of ice change per decade, calculated from data for the entire
    satellite period.

    All of the daily data for each month is used to compute a standard deviation
    grid, where each gridcell's value is the standard deviation of that gridcell
    across the concentration values for the whole month. A gridcell with a high
    value here indicates that the ice was melting or growing rapidly in that
    month at that location.

    The trend is computed with weighted least squares regression. 1/(standard
    deviation^2) is used for the weights, so that months that had more rapidly
    changing ice have less of an impact on the computed trend values for those
    gridcells that were changing rapidly.

    Monthly data is returned from a single monthly data file after checking its
    validity. When a monthly file does not exist, the daily files are averaged
    to create the monthly concentration. Final daily files are used when
    available, otherwise near real time daily files are used.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy array for the trend.

    'metadata' contains another dictionary with various information about the
    grid, including the files used to create it.

    Keyword Arguments:
    ----------------
    hemisphere               -- nt.NORTH or nt.SOUTH

    year                     -- Integer year (4 digits)

    month                    -- Integer month number.

    search_paths             -- List of directories that will be recursively searched for
                                nasateam sea ice concentration files.

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.

    trend_start_year         -- Integer year (4 digits) representing the earliest year to
                                consider when calculating trends. Defaults to the first
                                year data is available for the selected month.

    clipping_threshold   -- integer representing absolute value of threshold
                            outside of which values will be clipped to the
                            threshold.

    """
    return trend.trend_gridset(hemisphere, year, month, search_paths,
                               min_days_for_valid_month, trend_start_year,
                               clipping_threshold=clipping_threshold)


def concentration_seasonal_trend(hemisphere=None, year=None, season=None,
                                 search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                                 seasons=nt.SEASONS,
                                 min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
                                 *, clipping_threshold):
    """Return a gridset containing the trend of concentration for the given season
    in percentage of ice change per decade, calculated from data for the entire
    satellite period.

    All of the daily data for each season is used to compute a standard deviation
    grid, where each gridcell's value is the standard deviation of that gridcell
    across the concentration values for the whole season. A gridcell with a high
    value here indicates that the ice was melting or growing rapidly in that
    season at that location.

    The trend is computed with weighted least squares regression. 1/(standard
    deviation^2) is used for the weights, so that seasons that had more rapidly
    changing ice have less of an impact on the computed trend values for those
    gridcells that were changing rapidly.

    Monthly data is returned from a single monthly data file after checking its
    validity. When a monthly file does not exist, the daily files are averaged
    to create the monthly concentration. Final daily files are used when
    available, otherwise near real time daily files are used. Seasonal data is
    the average of monthly data for the relevant months.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy array for the trend.

    'metadata' contains another dictionary with various information about the
    grid, including the files used to create it.

    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    year                 -- Integer year (4 digits)

    season               -- string; 'spring', 'summer', 'autumn', or 'winter'

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    seasons              -- dictionary; key is a season name, value is a list of
                            integer months contained in that season; default is
                            nt.SEASONS, which has `'spring': [3,4,5]` and so on.

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.

    clipping_threshold   -- integer representing absolute value of threshold
                            outside of which values will be clipped to the
                            threshold.
    """
    return trend.seasonal_trend_gridset(hemisphere, year, season, search_paths,
                                        seasons, min_days_for_valid_month,
                                        clipping_threshold=clipping_threshold)


def extent_monthly(hemisphere=None, year=None, month=None,
                   search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                   extent_threshold=nt.EXTENT_THRESHOLD,
                   allow_empty_gridset=True, drop_land=False,
                   drop_invalid_ice=True, ensure_full_nrt_month=False,
                   min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing a monthly sea ice extent grid and metadata.

    Monthly data is returned from a single monthly data file after checking
    its validity. When a monthly file does not exist, the daily files are
    averaged to create the monthly concentration.  Final daily files are used
    when available, otherwise near real time daily files are used.

    The monthly extent grid is created from the final concentration grid,
    whether it was obtained from a single monthly file or averaged from daily
    files.

    When a month within the satellite era does not have enough valid data to
    be considered complete (e.g. Jan 1988), an empty data grid is
    returned. For requests before the satellite era or for the current or
    future months, an out of range error is raised.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy masked array for the monthly
    concentration.

    'metadata' contains another dictionary with a key 'files' that is a list
    of source files that went into creating the data grid.

    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    year                 -- Integer year (4 digits)

    month                -- Integer month number.

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception rather
                            than returning an empty_gridset() when no data is
                            available for the request.  Defaults to 'True'

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to True.

    ensure_full_nrt_month -- If 'True', raise a Exception rather than returning a
                             gridset that was created using a month with NRT data
                             and missing days

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.
    """
    gridset = getter.concentration_monthly(hemisphere, year, month, search_paths,
                                           min_days_for_valid_month)

    filters = _filters(hemisphere=hemisphere,
                       month=month,
                       drop_land=drop_land,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset,
                       extent_threshold=extent_threshold,
                       ensure_full_nrt_month=ensure_full_nrt_month)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def extent_monthly_median(hemisphere=None, start_year=None, end_year=None,
                          month=None, search_paths=nt.DEFAULT_SEA_ICE_PATHS,
                          extent_threshold=nt.EXTENT_THRESHOLD,
                          allow_empty_gridset=True, drop_land=False,
                          drop_invalid_ice=True,
                          min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH):
    """Return a gridset containing the median monthly sea ice extent grid and
    metadata.  This is generally called to compute the monthly climatolgical
    median ice extent.

    All monthly extents for the month: `month` between `start_year` and
    `end_year` inclusive are gathered and a single grid is returned
    representing the locations in the grid where ice was present 50% or more of
    the time.

    The returned gridset is a dictionary with two keys: 'data' and 'metadata'.

    Accessing the 'data' key yields the 2-d numpy masked array for the monthly
    median extent.

    'metadata' contains another dictionary with a key 'files' that is a list
    of source files that went into creating the data grid.

    Keyword Arguments:
    ----------------
    hemisphere           -- nt.NORTH or nt.SOUTH

    start_year           -- Integer year (4 digits)

    end_year             -- Integer year (4 digits)

    month                -- Integer month number.

    search_paths         -- List of directories that will be recursively searched for
                            nasateam sea ice concentration files.

    extent_threshold     -- The minimum concentration value that should be
                            counted as extent.

    allow_empty_gridset  -- If 'False', raise a SeaIceDataNoData exception rather
                            than returning an empty_gridset() when no data is
                            available for the request.  Defaults to 'True'.

    drop_land            -- If 'True', replace land and coast values (from
                            nt.FLAGS) with 0. Defaults to False.

    drop_invalid_ice     -- If 'True', apply the climatological mask for invalid
                            ice, replacing ice values covered by the mask with
                            0. Defaults to True.

    min_days_for_valid_month -- The number of days in a year-month for which
                                daily files must exist for the monthly data to
                                be considered valid. Defaults to
                                nt.MINIMUM_DAYS_FOR_VALID_MONTH.
    """
    gridset = getter.extent_monthly_median(hemisphere, start_year, end_year,
                                           month, search_paths,
                                           extent_threshold, min_days_for_valid_month)

    filters = _filters(hemisphere=hemisphere,
                       month=month,
                       drop_land=drop_land,
                       drop_invalid_ice=drop_invalid_ice,
                       allow_empty_gridset=allow_empty_gridset)

    gridset = gf.apply_filters(gridset, filters)

    return gridset


def _filters(*,
             hemisphere=None,
             month=None,
             start_year=None,
             end_year=None,
             dayofyear=None,
             drop_land=None,
             allow_bad_dates=None,
             interpolation_radius=0,
             drop_invalid_ice=None,
             allow_empty_gridset=None,
             extent_threshold=None,
             ensure_full_nrt_month=None):
    filters = []

    if drop_land is True:
        filters.append(functools.partial(gf.drop_land, nt.FLAGS['land'], nt.FLAGS['coast']))

    if allow_bad_dates is False:
        filters.append(gf.drop_bad_dates)

    if interpolation_radius > 0:
        filters.append(gf.interpolate)

    if drop_invalid_ice is True:
        if None not in [hemisphere, month]:
            invalid_ice_mask = nt.invalid_ice_mask(hemisphere, month)
        elif None not in [start_year, end_year, dayofyear, hemisphere]:
            invalid_ice_mask = _invalid_ice_mask_for_median(start_year,
                                                            end_year,
                                                            dayofyear,
                                                            hemisphere)
        else:
            invalid_ice_mask = None

        if invalid_ice_mask is not None:
            filters.append(functools.partial(gf.drop_invalid_ice, invalid_ice_mask))

    if extent_threshold is not None:
        filters.append(functools.partial(gf.concentration_to_extent, extent_threshold))

    if allow_empty_gridset is False:
        filters.append(gf.prevent_empty)

    if ensure_full_nrt_month is True:
        filters.append(gf.ensure_full_nrt_month)

    return filters


def _anomaly_gridset(month_gridset, climatology_gridset):
    def masked_data(gridset):
        """Return gridset's data with everything outside the valid range masked"""
        return np.ma.masked_outside(gridset['data'], *gridset['metadata']['valid_data_range'])

    def flags_only(gridset):
        """Return gridset's data with everything in the valid range masked"""
        return np.ma.masked_inside(gridset['data'], *gridset['metadata']['valid_data_range'])

    def largest_pole_hole(month_gridset, climatology_gridset, pole_hole_value):
        """Returns a 2D boolean np array where True values represent the largest
        pole hole found between the month_gridset and climatology_gridset.
        """
        climatology_pole_hole = np.any(climatology_gridset['data'] == pole_hole_value, axis=2)
        month_pole_hole = month_gridset['data'] == pole_hole_value

        return np.logical_or(climatology_pole_hole, month_pole_hole)

    climatology_grid = masked_data(climatology_gridset).mean(axis=2)
    climatology_grid = grid_filters.concentration_cutoff(nt.EXTENT_THRESHOLD, climatology_grid)

    # take the difference of masked grids, so that land and pole hole aren't
    # included in the subtraction
    anomaly_grid = masked_data(month_gridset) - climatology_grid

    # fill in the mask with land and pole hole
    flag_layer = getter.flag_layer_from_cube(flags_only(climatology_gridset), nt.FLAGS['missing'])
    anomaly_grid = anomaly_grid.filled(flag_layer)

    # Apply the largest pole hole to the anomaly_grid.
    pole_hole_value = month_gridset['metadata']['flags']['pole']
    pole_hole = largest_pole_hole(month_gridset, climatology_gridset, pole_hole_value)
    anomaly_grid[pole_hole] = pole_hole_value

    metadata = copy.deepcopy(month_gridset['metadata'])
    metadata['month_files'] = metadata.pop('files')
    metadata['month_period_index'] = metadata.pop('period_index')
    metadata['climatology_files'] = climatology_gridset['metadata']['files']
    metadata['climatology_period_index'] = climatology_gridset['metadata']['period_index']
    metadata['type'] = 'Monthly Anomaly'

    valid_data_min = (month_gridset['metadata']['valid_data_range'][0] -
                      climatology_gridset['metadata']['valid_data_range'][1])

    valid_data_max = (month_gridset['metadata']['valid_data_range'][1] -
                      climatology_gridset['metadata']['valid_data_range'][0])

    metadata['valid_data_range'] = (valid_data_min, valid_data_max)

    gridset = {
        'data': anomaly_grid,
        'metadata': metadata
    }

    return gridset


def _invalid_ice_mask_for_median(start_year, end_year, dayofyear, hemisphere):
    full_date_range = pd.date_range(start=str(start_year), end=str(end_year + 1))

    doys = full_date_range[full_date_range.dayofyear == dayofyear]
    month = mode(doys.month)

    invalid_ice_mask = nt.invalid_ice_mask(hemisphere, month)

    return invalid_ice_mask
