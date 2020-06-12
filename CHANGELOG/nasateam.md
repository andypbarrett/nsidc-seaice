# v2.5.0 (2017-11-21)

* add function `validate_seasons` to ensure a possible user-defined `dict` of
  seasons is valid and will work with the code in `seaicedata` and
  `seaiceimages`

# v2.4.0 (2017-11-21)

* add constant `SEASONS`, a hash that maps season names (`str`) to a tuple of
  months (`int`) that make up the season
* add function `datetime_index_for_seasonal_trends`, which returns a
  `Pandas.DatetimeIndex` containing every day that is part of the season, from
  the beginning of the monthly satellite era through the latest year in which
  that season is complete

# v.2.3.0 (2017-08-09)

* add environmental variable `OVERRIDE_NASATEAM_CONSTANTS`. This variable can
  be set to the full filename of a python module.  Any variables found in the
  module will be loaded, overriding any values already set in constants.  This
  can be used to change hard to reach configuration.

# v2.2.0 (2017-08-02)

* Add `__version__` property (PEP 396)
* Add constant `BAD_CONCENTRATION_MONTHS` to deal with the special case of
  August 1987, where because of the pole hole change within the month, we are
  uninterested in its monthly area value and images in the northern hemisphere,
  but are interested inall of the other monthly values/images for the month.

# v2.1.0 (2017-07-18)

* Add changes from v1.3.0 to v2.0.0

# v1.3.0 (2017-07-05)

* Add constant `LAST_DAY_WITH_VALID_FINAL_DATA`, currently set to 2015-12-31. In
  April 2016, some f17 issues were discovered and f18 became the preferred
  platform. In March 2017, NSIDC-0051 was updated with final f17 data for
  January 2016 through February 2017. For the period of January 2016 through
  March 2016, near-real-time data is still preferred to the questionable final
  f17 data. This new constant provides more fine-grained control than was
  available with just `PLATFORM_RANGES`.
* Add constant `SMMR_DAYS`, containing the days in the SMMR period that should
  have ice (since we only have files for every other day, the days without data
  are excluded from this constant).

# v2.0.0 (2017-06-22)

* Change constant `VERSION_STRING` to `'v3.0'` for Sea Ice Index v3.

# v1.2.0 (2017-05-04)

* Add constant `BEGINNING_OF_SATELLITE_ERA_YEARLY` for 1979-01-01, the start of
  the first full year of data.

# v1.1.1 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v1.1.0 (2017-01-09)

* switched SII version to 2.1

# v1.0.1 (2017-01-03)

* Updated documentation

# v1.0.0 (2016-12-15)

* Add constants `SEA_ICE_BASE_DIR`, `BLUE_MARBLE_PICKLE_DIR`, and
  `BLUE_MARBLE_PICKLE_PATH`. `BLUE_MARBLE_PICKLE_PATH` must be interpolated with
  a value for `hemi` (`'north'` or `'south'`).
* Add f18 sensor to the PLATFORM_RANGES constant.
* Gracefully deprecate `DAILY_DATA_STORE_FILENAME` and `MONTHLY_DATA_STORE_FILENAME`
  in favor of the more concise `DAILY_DATA_STORE_PATH` and `MONTHLY_DATA_STORE_PATH`
* Relocate DATA_STORE_BASE_DIRECTORY from SEA_ICE_BASE_DIR/timeseries to
  SEA_ICE_BASE_DIR/datastore

# v0.5.1 (2016-11-19)

* Change constant `DATA_STORE_BASE_DIRECTORY` to point to new /share/apps/seaice/timeseries location

# v0.5.0 (2016-11-04)

* Change constant `DAILY_DATA_STORE_FILENAME`, `MONTHLY_DATA_STORE_FILENAME` to point to new pickled datastore defaults
* Add constant `BEGINNING_OF_SATELLITE_ERA_MONTHLY`

# v0.4.0 (2016-09-13)

* renames constant `STATISTICS_COLUMNS` => `DAILY_DEFAULT_COLUMNS`
* removes constant `DATA_COLUMNS`
* adds `failed_qa` to `DAILY_DEFAULT_COLUMNS`
* adds constant `MONTHLY_DEFAULT_COLUMNS` that is `DAILY_DEFAULT_COLUMNS` without the `failed_qa` column.

# v0.3.0 (2016-08-11)

* Add convenience function `by_name` to return a NORTH or SOUTH hemisphere
  object by name.

* Add function `shore_mask` to return dilated land regions as
  shore/near_shore/off_shore

* Add function `loci_mask` to return the "land ocean coast ice" mask from
  NSIDC-0622 in the northern hemisphere and the appropriate analog for the
  southern hemisphere.

* Add function `invalid_ice_mask` to return 2D numpy arrays of the masks in
  NSIDC-0622. Previously, this function was in the `sedna` package.

* Add constant `VERSION_STRING`

* Add constant `SMMR_PLATFORM`

* Add key `crs` to hemisphere dicts.

* Add key `transformation_constants` to hemisphere dicts.

# v0.2.0 (2016-03-15)

* Add `METADATA_COLUMNS` constant to identify non-interpolatable columns.

# v0.1.1 (2016-02-16)

* Split constants into logical-ish units.
