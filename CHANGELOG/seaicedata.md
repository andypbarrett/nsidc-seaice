# v3.7.0

* Add CLI `monthly_files_from_dailies` to create monthly concentration grid
  files in binary format. A text file with metadata about the command and binary
  files is also created.

# v3.6.0 (2017-11-21)

* Add function `concentration_seasonal_trend`, which returns a gridset
  representing the sea ice concentration trend in a given season, from the
  beginning of the satellite record to the specified year. Seasonal
  concentration is the average of the monthly concentrations for the months that
  make up that season; for each year, the seasonal concentration is taken, then
  a trend across the years is calculated for each pixel in the same manner that
  monthly trend is computed.

# v3.5.0 (2017-08-17)

* Change filtering of prefered platform.  Now enforces platform filtering to
  the ranges defined in nasateam's PLATFORM\_RANGES.  That means that if a
  single file is found that has a platform that falls outside of the values in
  nasateam's PLATFORM\_RANGES, no data is returned.
* Fix `getter.flag_layer_from_cube()` to not use the first layer in the cube as
  the basis for the flag layer if the first layer happens to be all missing;
  instead, use whichever layer comes first *and* is not all missing.

# v3.4.3 (2017-08-02)

* Add `__version__` property (PEP 396)
* Return the empty gridset for `concentration_monthly(nt.NORTH, 1987, 8)`, due
  to the pole change that occurs part way through the month. Other grids for
  1987-08 are unaffected.

# v3.4.2 (2017-07-25)

* Fix `getter.concentration_monthly` to properly handle
  `nt.LAST_DAY_WITH_VALID_FINAL_DATA`; it was still returning grids from the
  final data, but now it will return a grid representing the average of the
  daily grids if the month falls after the valid final data cutoff.

# v3.4.1 (2017-07-18)

* Add changes from v3.3.4 to 3.4.0

# v3.3.4 (2017-07-05)

* Use `nt.LAST_DAY_WITH_VALID_FINAL_DATA` to only use final data up to the
  specified date. This was done to address f17 issues discovered in April 2016;
  final data from f17 was recently added for January 2016 through February 2017,
  and while `nt.PLATFORM_RANGES` ensures that f18 near-real-time data will be
  used for April 2016 through the present, without this change the final f17
  data is used for January 2016 through March 2016, which should be avoided for
  the time being.

# v3.4.0 (2017-06-22)

* Update `nasateam` dependency to >=2.0 for Sea Ice Index v3.0
* Raise an error if the passed `search_paths` is a string. The `nasateam`
  constants used for default search paths are lists of strings, and the code
  iterates over this list; if a string is passed, this resulted in the unwanted
  behavior of iterating over the string, so each character in the string would
  be treated as its own search path. That's never intended, so raise an error
  when a string is passed.
* Log warnings when an empty grid is returned for monthly data due to that month
  having insufficient daily files (thanks December 1987 and January 1988).
* Add parameter `min_days_for_valid_month` to monthly API calls. It defaults to
  `nt.MINIMUM_DAYS_FOR_VALID_MONTH`, maintaining past behavior, but allows users
  to pass any number, and thus work with monthly data even if there aren't
  enough daily files in their `search_paths`.

# v3.3.3 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v3.3.2 (2017-01-03)

* Update documentation

# v3.3.1 (2016-12-19)

* `concentration_daily_average_over_date_range` returns an empty gridset if no
  files are found for the given date range.

# v3.3.0 (2016-12-15)

* Add 'allow_empty_gridset' parameter to concentration_monthly_anomaly
  api. A SeaIceDataNoData error will be now be thrown if the grid is missing
  data and this flag is set to False.
* Relocate /share/apps/g02135-sii-asina to /share/apps/seaice
* Relocate /share/logs/g02135-sii-asina to /share/logs/seaice
* Export gridset_filters as filters.
* Add api function `concentration_daily_average_over_date_range` to get the
  average concentration grid over a specified date range, which can be used in
  the Science on a Sphere images.
* Fix `drop_bad_dates` gridset filter so it works with gridsets containing
  double-weighted SMMR files.

# v3.2.0 (2016-11-17)

* Add standard Python logging.
* Code refactoring.
* Support for pandas 0.19.0
* Fix `valid_data_range` in a gridset's metadata to be scaled when the data
  itself is scaled; nsidc-0051 and nsidc-0081 are stored in binary as values
  between 0 and 250, but we immediately scale that to 0-100.
* Add API function `concentration_monthly_anomaly`, which returns a gridset
  showing the difference between the concentration for a given month and the
  climatological mean for that month.
* Add more metadata to daily median extent gridsets.
* Add API function `concentration_monthly_trend`, which returns a gridset
  showing the trend in concentration for a particular month from the start of
  the satellite period to the current year.
* Fix the gridset filters `apply_largest_pole_hole` and `drop_invalid_ice` to
  not affect empty grids.


# v3.1.2 (2016-09-13)

* Remove errant print statement.

# v3.1.1 (2016-09-13)

* Fix interpolation for days in SMMR period that don't have files. Interpolation
  is not needed for normal daily concentrations, but it is used for climatology
  median calculations.

# v3.1.0 (2016-09-13)

* Updated daily interpolation logic to handle bad data cases correctly when
  disallowing bad data.
* Move nasateam-related constants out of `seaicedata` into a separate package,
  `nasateam.`
* Double-weight SMMR daily files by adding them a second time to the list of
  files used by the function `getter.monthly_concentration` This accounts for
  SMMR daily files only appearing every other day when we are concerned with
  having enough data for a valid month, or averaging data when there is a
  satellite changeover.
* Fix bug where a platform not listed in `nt.PLATFORM_RANGES` causes a crash.
* Add functions `extent_daily` and `extent_monthly` to return gridsets with
  extent values rather than concentration values.
* Add function `extent_daily_median` to return a daily extent median gridset for
  many years.
* Add keyword argument to all API calls `allow_empty_gridset` that defaults to
  True, but when is provided with `False` causes the software to raise a
  `SeaIceDataNoData` exception.
* Move functions that return cubes of data over years out of `api` module and
  into a separate module. These functions are less important and do not need to
  be included immediately when importing `seaicedata`.
* Add function `extent_monthly_median` to return a monthly extent median gridset
  for many years.
* Change interface of functions that get daily data over a range of years to
  accept a `dayofyear` parameter, and not `month` and `day` parameters.
* Add functions to manage a file with a list of dates known to contain bad data.
* Add parameter `allow_bad_dates` to daily data accessor functions; if `False`,
  (the default value), the empty gridset will be returned for dates in the list
  of known bad dates. If `True`, the faulty data file will be loaded and
  returned.
* Add parameter `drop_land` to API functions; if `True`, land and coast values
  will be returned as `0` instead of their normal `nt.FLAGS` values. Defaults to `False`.
* Add parameter `drop_invalid_ice` to API functions; if `True`, ocean gridcells
  marked invalid by the climatology valid ice mask will be returned as `0`
  instead of the concentration value found in the 0051/0081 files. Defaults to
  `False` for concentration functions and `True` for extent functions.

# v3.0.0 (2016-02-09)

* Change the nasateam hemisphere to use uppercase letters for the hemisphere
  short names.

# v2.0.0 (2016-01-25)

* Change how special flag values are managed.

# v1.1.0 (2016-01-19)

* Fix masked data when interpolating.  We need more than just masked/unmasked
  in order to properly handle pole hole and missing data.  Therefore we only
  interpolate missing data and retain other flagged data as it was.  This
  presumes that the land/coast/lake/pole masks are identical for all layers
  in the interpolation.  Meaning, that we will compute an average value
  across land, but it should be land in each layer and therefore the average
  value will be identical to the single layer value.

# v1.0.2 (2015-12-29)

* Add caching to functions that return data frames from a list of files.
* Internal speed improvements during indexing.

# v1.0.1 (2015-12-16)

* Fix bug where locating monthly files did not work for months with multiple
  files (e.g., v01 monthly files in 2007, where each month has file for f13
  and one for f17)
  ([#23](https://bitbucket.org/nsidc/seaicedata/pull-requests/23/))

# v1.0.0 (2015-12-01)

* Initial release.
