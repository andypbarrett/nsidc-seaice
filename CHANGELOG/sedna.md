# v3.1.1 (2017-10-17)

* Fix bug for CLIs where if no configfile was given, or no `search_paths` key
  was found in the configfile, the `search_paths` were set to `[]`. This caused
  the command `update_sea_ice_statistics_daily` to fail to find any data files,
  and therefore all data for the relevant days was set to `NaN`s.
* Add changes from v2.3.6 to v3.1.0

# v2.3.6 (2017-08-14)

* When computing regional monthly data, if a region is masked out by the invalid
  data mask (i.e., NSIDC-0622), use `0` instead of `NaN` for the area, extent,
  and missing values. (the change in v2.3.4 only applied to daily data)

# v3.1.0 (2017-08-02)

* Add `__version__` property (PEP 396)
* Total area in the North and regional area for the Central Arctic region are
  set to `NaN` for 1987-08 due to the changing pole hole.

# v3.0.1 (2017-07-18)

* Add changes from v2.3.4 and v2.3.5 to v3.0.0

# v2.3.5 (2017-07-05)

* Update the documentation for `--interpolation_radius` on
  `update_sea_ice_statistics_daily`.
* Use `nt.LAST_DAY_WITH_VALID_FINAL_DATA` to get the proper final date for which
  finalized data (NSIDC-0051) should be used in
  `initialize_sea_ice_statistics_daily`.
* For the regional data change in v2.3.4, only use `0` for days where data is
  fully expected--for every other day in the SMMR period, where the full day is
  missing, don't replace the `NaN` with `0`.

# v2.3.4 (2017-06-30)

* When computing regional data, if a region is masked out by the invalid data
  mask (i.e., NSIDC-0622), use `0` instead of `NaN` for the area, extent, and
  missing values.

# v3.0.0 (2017-06-28)

* Change the method of computing monthly values. Final data no longer uses the
  monthly files, and near-real-time data no longer computes an average
  grid. Instead, start with the daily values computed from daily files, then
  take the average over the days in a given month.
* Replace CLIs `initialize_sea_ice_statistics_monthly` and
  `update_sea_ice_statistics_monthly` with `sea_ice_statistics_monthly`. With
  the new method, there is little time advantage to calculating the statistics
  for just a range of months instead of the whole time series, so to simplify
  things there is now only one monthly endpoint.
* Update `nasateam` dependency.

# v2.3.3 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v2.3.2 (2017-01-03)

- Explicitly constrain dateutil dependency version.
- Updated documentation

# v2.3.1 (2016-12-20)

- Added 'force_missing_nrt' to default config as bugfix for datastore initialization.

# v2.3.0 (2016-12-15)

- Added --force_missing_nrt_days to sedna monthly update command to override
  new seaicedata nrt check
- Included use of seaicedata ensure_full_nrt_month filter in monthly processing
  to prevent creation of near-real-time monthly stats when the month is not
  complete
- relocated /share/apps/g02135-sii-asina &  /share/logs/g02135-sii-asina
- More logging when updating daily and monthly statistics, so that it is more
  clear that the program is not hanging.

# v2.2.3 (2016-11-04)

- Switched to picked datastore.
- Update to pandas 0.19.

# v2.2.2 (2016-10-05)

- Initialize will now write to a temp file, then move the data in place to
  minimize downtime
- Areal values are no longer rounded to integers before being stored in the
  datastore; 3 decimal places are kept.

# v2.2.1

- Daily initialization no longer sets a QA flag for the 'final data' period.
- Started using seaicelogging package, logs are now written to
  /share/logs/g02135-sii-asina/sedna.log


# v2.1.2 (2016-09-13) / v2.2.0 (2016-09-15)

*this should have been a minor version change, but was mistakenly released as a
patch version, then re-released with the correct version*

- Monthly initialization now selects correct complete start month, based on
  nasateam configuration
- Preserves existing datastores when
  `_initialize_sea_ice_statistics_[daily|monthly]` runs. An existing datastore
  filename is postpeded with a timestamp before a new datastore file is
  created.
- Add `failed_qa` column to daily datastores and set it to 'False' on update.
- Add `validate_daily_data` command that will validate a daily sedna datastore csv
  against a configurable linear regression and optionally update the datastore
- Modify the `update_sea_ice_statistics_daily` command such that it will run
  the linear regression evaluation on every updated day and mark the `failed_qa`
  column in the datastore appropriately.

# v2.1.1

- Remove function `_invalid_ice_mask`; instead, import `invalid_ice_mask` from
  the `nasateam` package.
- Stop writing `--` to the csv files.

# v2.1.1

- Add dependency on nasateam package
- Move constants into nasateam package
- Move regional mask binary file into nasateam package
- Change `ConcentrationCube._extent_binary_grid` so that valid concentration
  values that are below the threshold (15%) are converted to 0 rather than
  masked. This led to an issue where regional extents and areas were being
  computed as NaN rather than 0.

# v2.1.0 (2016-02-10)

- Add new column "source_dataset" to output; values are "nsidc-0051" or
  "nsidc-0081"

# v2.0.0 (2016-02-09)

- Update regression tests to use all v1.1 data, instead of some v01 and some
  v1.1 data
- Use capital letters for the hemispheres

# v1.1.1 (2016-01-28)

- Fix issue where extent for missing data would be calculated as 0 km^2 rather
  than NaN.

# v1.1.0 (2016-01-26)

- Update how gridsets from seaicedata are handled; the structure of their data
  and metadata has been changed for a better separation of data and flag values.
