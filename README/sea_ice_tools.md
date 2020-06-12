sea_ice_tools
-------------

**sea_ice_tools** contains a variety of tools for generating spreadsheets, data
CSV files, and time series plots from [Sea Ice
Index][sii](http://nsidc.org/data/seaice_index/) data.

![CLI Diagram](doc/HighLevelArchitecture.png)
([Created on Lucid Chart](https://www.lucidchart.com/documents/edit/aca6b078-3059-4ca4-bda8-4515ae7a5a4d?shared=true&))

# Usage

## CLI

This table shows the CLI commands included in this package, and the files they
create. For more information on the available options for each command, use the
`--help` flag.

| CLI                           | Output file
|-------------------------------|------------
|`sea_ice_climatology_csvs`     | `{H}_seaice_extent_climatology_1981-2010_{ver}.csv`
|`sea_ice_extent_daily_csvs`    | `{H}H_seaice_extent_daily.csv`
|`sea_ice_extent_monthly_csvs`  | `{H}_{MM}_area.csv`
|`plot_daily_ice_extent`        | `daily_ice_extent_{hemi}.png`
|`plot_monthly_ice_anomaly`     | `{H}_{MM}_extent_anomaly_plot_{ver}.png`
|`plot_monthly_ice_extent`      | `monthly_ice_{H}H_{MM}.png`
|`regional_daily`               | `Sea_Ice_Index_Regional_Daily_Data_G02135_v3.0.xlsx`
|`regional_monthly`             | `Sea_Ice_Index_Regional_Monthly_Data_G02135_v3.0.xlsx`
|`daily_extent`                 | `Sea_Ice_Index_Daily_Extent_G02135_v3.0.xlsx`
|`monthly_with_statistics`      | `Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_v3.0.xlsx`
|`min_max_rankings`             | `Sea_Ice_Index_Min_Max_Rankings_G02135_v3.0.xlsx`
|`rates_of_change`              | `Sea_Ice_Index_Rates_of_Change_G02135_v3.0.xlsx`
|`monthly_by_year`              | `Sea_Ice_Index_Monthly_Data_by_Year_G02135_v3.0.xlsx`

There are two additional CLI commands in this package that wrap the commands
listed above:

* `process_latest_daily` wraps the necessary commands to generate the latest daily files
* `process_latest_monthly` wraps the necessary commands to generate the latest monthly files

# Development

## Reader module

The `reader` module provides the function `read` which can read any of the
`.csv` and `.xlsx` output files listed in the CLI section. This is useful for
verifying the contents of those files, or for comparisons when making code
changes.

```
from seaice.tools.reader import read

monthly_by_year_dfs = read('Sea_Ice_Monthly_by_Year_G02135_v3.0.xlsx')
daily_extent_df = read('NH_seaice_extent_daily.csv')

# if you have a file whose name doesn't match but it's contents do, just pass
# the normal filename as a second argument to read
daily_extent_df = read('my_weirdly_named_file.csv', 'NH_seaice_extent_daily.csv')
```
