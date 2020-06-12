# v1.3.1 (2017-08-10)

- Update `rasterio` dependency. `rasterio 1.0a3` was removed (along with all
  other 1.x versions) from the conda-forge main channel. `1.0a9` has been added
  to the conda-forge dev channel, and future `1.0a` releases will be published
  there as well.

# v2.1.0 (2017-08-03)

- Add `__version__` property (PEP 396)
- Add `--version` flag to CLI
- Update `rasterio` dependency. `rasterio 1.0a3` was removed (along with all
  other 1.x versions) from the conda-forge main channel. `1.0a9` has been added
  to the conda-forge dev channel, and future `1.0a` releases will be published
  there as well.

# v2.0.0 (2017-06-27)

* Update `nasateam` dependency for Sea Ice Index v3.
* Filenames output `v3.0` instead of `v2.1`.

# v1.3.0 (2017-06-01)

* Add `contour_value` parameter to `multipolygon_daily` and `multipolygon_monthly`
  api functions, allowing the creation of multipolygons around other features (e.g.,
  missing values)

# v1.2.1 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# v1.2.0 (2017-01-09)
* change output version to v2.1

# v1.1.0 (2017-01-04)
* Add --date-range flag to sii_shp cli to allow generating
  monthly shapefiles over a range of dates.

# v1.0.2 (2017-01-03)
* Documentation update

# v1.0.0 (2016-12-15)

* Use /share/apps/seaice/datastore instead of
  /share/apps/seaice/timeseries in project ci

# v0.1.3 (2016-11-17)

* Relocate /share/apps/g02135-sii-asina to /share/apps/seaice
* Relocate /share/logs/g02135-sii-asina to /share/logs/seaice

# v0.1.2

* Upgrade pandas to 0.19.0.
* Remove lakes from daily median shapefiles.

# v0.1.1 (2016-10-10)

* Utilize seaicelogging package to create log/stdout output
* Don't exit with failure if the only problem was skipping shapefiles due to the
  SeaIceDataNoData exception.
* When exiting with failures, raise a more descriptive exception and list the
  other exceptions that were caught during executiong.

# v0.1.0 (2016-09-13)

* Add CLI command and invoke tasks to generate monthly sea ice extent
  polygon and polyline shapefiles.
* Add CLI command and invoke task to generate daily polyline shapefiles for
  median climatology sea ice extent.
* Add CLI command and invoke task to generate monthly polyline shapefiles for
  median climatology sea ice extent.
* Add API functions to get Shapely polygon objects for a given date, or a given
  year-month.
