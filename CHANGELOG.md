# v2.3.1

* Loosen dependencies to previous constraints, but keep icu exact pin
# v2.3.0

* Output two regional spreadsheets (North/South) instead of one
  * New `region_s` regional mask for Antarctic
* Improved logging/error-handling for finding last date with final data

# v2.2.1

* Fix clipping to apply after calculating decadal trend

# v2.2.0

* Add `--trend-clip` CLI and API option (default 100) to constrain maximum and
  minimum trend values.

# v2.1.3

* Switch from processes to threads so calling programs can use multiprocessing
  to spread load across many cores.

# v2.1.2

* Update conda dependencies
* Update default sea ice paths to use the /ecs/DP1 datapool.
* Update nasateam constants defining NRT / Final data date ranges. The last day
  with valid final data is now 2018-12-31.

# v2.1.1

* Added (hopefully temporary) libgfortran-ng=7.2.0 dependency. GDAL does not work without it.
* Fixed bug with `seaice.data.locator._find_all_nasateam_ice_files` no longer
  having the `cache_clear` method. `seaice.data.cache.SeaiceFsCache` now supports
  the `cache_clear` method for the default `lru_cache`.

# v2.1.0

* Added `data.cache.define_seaice_fs_cache` function, which allows users to define
  a custom caching backend for `locator._find_all_nasateam_ice_files`

# v2.0.2

* Fixed bug that prevented some polyline ice extent shapefiles from being
  created. The upgraded version of the `fiona` library (fiona >=1.8.0) does not
  accept `LineString` objects being written to shapefiles with a
  `MultiLineString` schema. Prior to upgrading, `fiona` would silently cast
  `LineString` objects to `MultiLineString`.

* Bugfixes related to pandas upgrade for excel files produced by
  seaice.tools. Index labels that had not been included in previous pandas
  versions were being added in undesirable locations. For consistency with
  previous versions, remove those from dataframes before converting to xlsx.


# v2.0.1

* Upgrade gdal dependency >=2.4.0. Builds <2.4.0 tend to be broken.

# v2.0.0

* Upgrade pandas dependency from v0.19.2 -> v0.24.1. See
  https://pandas.pydata.org/pandas-docs/version/0.24.0/whatsnew/index.html for
  complete details. Given that some of the seaice API return pandas dataframes,
  code using this version of `seaice` should be aware of the potentially
  breaking changes introduced by this upgrade.

* seaice.timeseries.api.daily's `interpolate` kwarg has been updated to be
  consistent with panda's df.interpolate. A value of `interpolate` <= 0
  indicates that no interpolation should be performed and a value of `None`
  fills any missing values regardless of the number of consecutive missing
  values. Previously, a value of 0 or None would fill any missing values. See
  the docstring of `daily` for complete details.

* Various performance improvements targeted at reducing processing time for
  trends to be calculated.

# v1.6.0

* Add sii_image_geotiff cli support for trend images.

# v1.5.0 (2018-12-21)

* v1.5.0 because of difficulties on Anaconda. Accidently pushed a number of tags
  instead of the one intended (v1.3.1). Ignore v1.3.1, v1.3.2, and v.1.4.0

* Upgrade plotly to v3.4.2. Previous version (v1.12.12) stopped working,
  apparently due to a breaking change on the plotly servers that made it
  impossible to generate titles.

# v1.4.0 (2018-12-21 - DO NOT USE)

* Released but should not be used. Tag was accidently pushed to master,
  resulting in a build of non-production ready code.

# v1.3.2 (2018-12-21 - DO NOT USE)

* Released but should not be used. Tag was accidently pushed to master,
  resulting in a build of non-production ready code.

# v1.3.1 ()

* Not released.

# v1.3.0 (2018-09-14)

* Add new trend_start_year option to seaice.data.concentration_monthly_trend,
  which determines the first year of data to consider when calculatitng
  trends. Also added trend_start_year option to seaice images CLI and API.

# v1.2.4 (2018-08-06)

* Update nasateam.LAST_DAY_WITH_VALID_FINAL_DATA to 2017-12-31, update platform
  ranges: f17 end date is 2017-12-31, f18 start date is 2018-01-01.
* Fix bug where data.api.concentration_monthly_anomaly returned an anomaly
  gridset with a too-small pole hole in situations where the chosen climatology
  has a smaller pole hole than the selected month/year grid.


# v1.2.3 (2018-07-25)

* CLIs with a directory or file argument or option now require the given value
  to be the proper type instead of any kind of path `click.Path`'s
  `dir_okay=False` or `file_okay=False` arguments). This causes the CLI to
  immediately exit with an error and a sensible message.

# v1.2.2 (2018-07-23)

* Update `rasterio` dependency to v1.0.0
* Update `click` dependency to v6.7

# v1.2.1 (release removed from Anaconda)

This release included an incorrect fix for v1.2.0; a fix was made on the conda
side, and v1.2.0 should be used instead of v1.2.1.

# v1.2.0 (2018-06-25)

* Change `PLATFORM_RANGES` values to be lists of tuples, rather than one
  tuple. This allows one platform to be preferred during multiple, separate time
  ranges; for example, preferring F17 in 2008-2016, and the brief periods in
  2018 where F18 was being tested and therefore not producing usable data.

# v1.1.0 (2018-05-04)

* Add jupyter to the `environment.yml`
* Add CLI `monthly_by_year_global` to produce a spreadsheet with monthly "global
  sea ice" extent values--sums of Northern and Southern Hemisphere extents.

# v1.0.0 (2018-05-02)

* Fix `--version` flag on all CLIs
* Documentation updates

# v0.1.0 (2018-04-24)

* Initial release with old sea ice packages grouped together into a single
  `seaice` package. Old packages are subpackages of `seaice`.
