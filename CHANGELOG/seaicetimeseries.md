# v1.0.7 (2017-06-27)

* Update `nasateam` dependency to >=2.0 for Sea Ice Index v3.0

# v1.0.6 (2017-06-06)

* Move the changes for v1.0.5 exclusively into
  `api.climatology_average_rates_of_change`; it now handles changing the index
  of the DataFrame returned from `api.monthly_rates_of_change`, keeping the
  desired functionality fix for clients of
  `api.climatology_average_rates_of_change`, and restoring the previous behavior
  of `api.monthly_rates_of_change` (v1.0.5 was actually a breaking change; this
  release fixes that).

# v1.0.5 (2017-06-06)

* Change the index of the DataFrame returned by `api.monthly_rates_of_change` to
  be a `DatetimeIndex` instead of a year/month `MultiIndex`. This fixes an issue
  where `api.climatology_average_rates_of_change` returned incorrect values due
  to averages being taken over all available data rather than the climatological
  period.

# v1.0.4 (2017-05-11)

* Add November 1978 back into monthly rates of change; this was broken in
  v1.0.3.

# v1.0.3 (2017-05-04)

* Don't include data from partial months (October 1978 and whatever the current
  month is) in the DataFrame returned by `api.monthly_rates_of_change`.

# v1.0.2 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v1.0.1 (2017-01-03)

- Update README

# v1.0.0 (2016-12-15)

- Relocate /share/apps/g02135-sii-asina to /share/apps/seaice
- Relocate /share/logs/g02135-sii-asina to /share/logs/seaice
- Added preserve_nan option to `daily` api that returns np.nan for
  all values that were originally missing values when the frame is
  being averaged with `nday_average`.  This update allows clients (e.g.
  seaiceservice) to request averaged values while retaining missing days
  as missing so that no value can easily be displayed for those days.

# v0.5.0 (2016-11-04)

- Require nasateam >= 0.5.0 and seaicedatastore >= 0.3.0 to support usage
  of new 'pickled' datastore

# v0.4.0 (2016-10-06)

- Remove parameter `restrict_filename` from function `daily`; there is no reason
  to cut down the filename in `seaicetimeseries`, but users of it can still do
  such manipulations.

# v0.3.0 (2016-09-13)

- Changes default imports.  No longer should you use statements like `import
  seaicetimeseries.api as sit`, now exposed routines are explicitly imported
  in `__init__.py` so that you can just import the package `import
  seaicetimeseries as sit`

- Requesting a smoothed timeseries from `daily` no longer returns NAN for the
  first values.  Smoothing now happens before date filtering, so that all
  available data is used before returning a subet to the user.

- `daily` and `monthly` now take a `columns` parameter that defaults to
  nt.API_DEFAULT_COLUMNS and by default will only return the whole hemisphere
  statistics.  If the parameter is set to be an empty list, all available
  columns are returned.

- Depends on package `nasateam` > 0.2.0.

- Adds `climatology_means` to API.

- API functions `normal_statistics` and `quantile` routines now take a pandas.Series, instead of a DataFrame.

- API functions `normal_statistics` and `quantile` routines generate statistics based on
  day of year, rather than on month/day.

- API function `quantile` now returns a DataFrame indexed on day of year with
  quantiles for the column names.

- Remove deprecated Pandas function `rolling_mean` with the appropriate Series
  and DataFrame methods.

- Internally change the way quantiles are computed, to work with Pandas 0.18.1
  while at the same time handling NaN values appropriately.

- Add parameter `restrict_filename` to function `daily`, to restrict the
  filename to current date, rather than a list of files used for interpolation.

# v0.2.1

- move constants to the nasateam package, add nasateam as a dependency
- add functions for climatology means, monthly anomaly, and monthly percent
  anomaly
- add 'trend' function to compute a best-fit line

# v0.2.0

- lists of filenames are parsed, so that the values in the returned dataframe
  are lists of strings, rather than strings
- the returned dataframe includes a new column, "source", with values "nrt" and
  "final", depending on the filenames for that row
- hemispheres are capitalized
- functions `monthly_rates_of_change` and `climatology_average_rates_of_change`
  taken from the package sea_ice_timeseries
- `scale` function added, to conveniently divide and round data columns
- constants added to common.py

# v0.1.0 (2015-12-24)

### Fetches and warps daily and monthly sea ice timeseries extent and area data.

- Retrieve Pandas dataframes of daily and monthly extent and area data.
- Interpolate missing days.
- Compute a trailing n-day average.
- Compute standard deviation and mean for a selected range of years.
- Compute quantile information for a selected range of years.
