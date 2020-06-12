# v4.1.0 (2018-04-10)

* Add CLI `daily_extent_global` to produce a spreadsheet with "global sea ice"
  values--sums of Northern and Southern Hemisphere values.

# v4.0.4 (2018-04-06)

* Bump matplotlib dependency for compatibility with [seaiceimages
  v2.5.1](https://bitbucket.org/nsidc/seaiceimages/pull-requests/131/downgrade-gdal-and-upgrade-matplotlib/diff).

# v4.0.3 (2017-08-16)

* Remove the plotly hotfix; the issue in plotly.js that necessitated this
  workaround was resolved ([github
  issue](https://github.com/plotly/plotly.js/issues/1907); [github
  PR](https://github.com/plotly/plotly.js/pull/1910)).

# v4.0.2 (2017-07-24)

* Apply the plotly hotfix to v4.0.1

# v3.10.0 (2017-7-21)

* HOTFIX for bug in plotly's api

# v4.0.1 (2017-07-18)

* Apply v3.9.1 changes to v4.0.0

# v3.9.1 (2017-06-30)

* Don't drop NaN rows from the regional DataFrame before writing the file. Fixes
  an issue for the St Lawrence region where rows were missing for November,
  December, much of August, and September 1, while the November and December
  values were mislabeled as September and October.

# v4.0.0 (2017-06-27)

* Bump `nasateam` dependency for Sea Ice Index v3.
* Files created by `sea_ice_tools` now include `v3` in their names, instead of
  `v2.1`.
* Add `precision` argument to
  `warp.seaicetimeseries_df_to_monthly_sea_ice_index_df`

# v3.9.0 (2017-06-06)

* Small updates to each of the excel files: new names and/or formatting of the
  files, sheets, and columns.
* Add `reader` module with `read` function that takes a path to an excel or csv
  file created by `sea_ice_tools`, and returns a pandas DataFrame or a
  dictionary of DataFrames parsed from the given file.

# v3.8.3 (2017-05-16)

* Add version string to generated `.xlsx` files.

# v3.8.2 (2017-05-11)

* Add documentation txt files to `MANIFEST.in` so they are packaged correctly.

# v3.8.1 (2017-05-11)

* Add `G02135` to the filename of all generated `.xlsx` files.

# v3.8.0 (2017-05-11)

* Update `seaicetimeseries` dependency to v1.0.3, so that the rates of change
  excel file will not include a value for the current month.
* Don't include October 1978 in the monthly rankings sheets of
  `Sea_Ice_Min_Max_Rankings.xlsx` since it is an incomplete month
* Don't include the current month in the monthly rankings sheets of
  `Sea_Ice_Min_Max_Rankings.xlsx` until it is complete; later days in the month
  may affect where the month ends up ranking
* Exclude 1978 and the current year from the annual rankings sheets of
  `Sea_Ice_Min_Max_Rankings.xlsx`
* Add a "Documentation" tab to every `.xlsx` file created.
* Create new spreadsheet with monthly data laid out by year,
  `Sea_Ice_Monthly_by_Year.xlsx`.
* In `Monthly_Sea_Ice_Index.xlsx`, include year and month values instead of
  blanking the whole row when the extent/area values are missing.
* Generate `Sea_Ice_Min_Max_Rankings.xlsx` and `Sea_Ice_Rates_of_Change.xlsx` in
  `process_latest_monthly` rather than `process_latest_daily`.

# v3.7.1 (2017-04-19)

* Updated `musher` dependency to v0.6.0
* Update slack configuration to use official nsidc slack for CI status notifications.

# 3.7.0 (2017-01-09)

- Update version string to v2.1 and use nasateam.VERSION_STRING where appropriate.
- Add attribution to monthly anomaly plot.

# 3.6.0 (2017-01-04)

- Update daily extent plot to show the date of the last good data rather than
  the target date

# 3.5.2 (2017-01-03)

- Fix dependency list; `python-dateutil` was not explicitly listed, but is used
  and should be properly version-constrained.
- Updated documentation.

# v3.5.1 (2016-12-20)

- Update version of [plotly](https://plot.ly/python/getting-started/) used to
  generate plots.

# v3.5.0 (2016-12-15)

- Added process_latest_daily command to run daily/monthly processing via a multiprocessing pool
- Daily extent csv command now only releases the joint file, file has been renamed
  to {hemisphere}_seaice_extent_v2.csv
- Change monthly .txt files to .csv format, change filename from {hemi}_{month}_area_v2.txt
  {hemi}_{month}_extent_v2.csv and remove 'note' at end of file
- Add choices for --standard_plot that create plots with IQR/IDR
- Change --standard_plot choices from "asina_n" and "asina_s" to "asina_north"
  and "asina_south"
- Silence numpy invalid value warnings when doing linear regressions with less than
  3 observations in warp.add_trends.
- Update paths to use nasateam directory constants instead of hard-coded paths
- Use nasateam.SEA_ICE_BASE_DIR/{datastore|csv|xls} instead of /share/apps/seaice/timeseries

# v3.4.0 (2016-11-17)

- Relocate /share/apps/g02135-sii-asina to /share/apps/seaice
- Relocate /share/logs/g02135-sii-asina to /share/logs/seaice
- Updates invoke tasks to add parameters for easier development work.
- Sets correct default sub-directories for output data.
- Renames climatology files:
-    `N_climatology_1981-2010_v2.csv` => `NH_seaice_extent_climatology_1981-2010_v2.csv`
-    `S_climatology_1981-2010_v2.csv` => `SH_seaice_extent_climatology_1981-2010_v2.csv`


# v3.3.0

- Requires Pandas >=0.19.0
- Utilizes serialized datastore/seaicedatastore >=0.3.0

# v3.2.0

- Add sea_ice_climatology generation command to create mean, std_dev and
  quantile csv output
- Update monthly area text files to have two decimal place output precision for
  area and extent columns
- Update .txt output to follow _v2 convention
- Update csv output to follow _v2 convention
- Fix formatting of day and month columns in `seaice_extent` CSV files; days and
  months with a single digit now have a leading zero.

# v3.1.0

- Add ability to plot interquartile and intercile ranges on the daily extent
  plots.
- Fix how the filenames are obtained for the daily sea ice extent CSVs.

# v3.0.1

- Add CHANGELOG
- Add dependency on nasateam package; use constants from nasateam where possible
  instead of defining them within this project.
- Add flake8-quotes to enforce a consistent single-quote style.
- Remove old testing data.
- Fix bug with generating the average monthly extent trend line where months
  with missing data were handled incorrectly.
- Adds `daily_regional` task and code to output daily regional excel sheets.
- Adds `monthly_regional` task and code to output monthly regional excel sheets.
- Change `plot_monthly_ice_extent` to use sedna's monthly output as the data
  source, and use plotly to generate Figure 3.
- Add `plot_monthly_ice_anomaly` to create the graph of extents in terms of
  their percentage difference from the climatological mean.
- Add `plot_daily_ice_extent` to create the graphs of daily sea ice extents.
- Fix regional output for daily and monthly generation.
