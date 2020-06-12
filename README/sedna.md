sedna
---

![sedna image](./assets/sedna-antony-galbraith.jpg)

[Sedna](https://mrpsmythopedia.wikispaces.com/Sedna/) exists to provide
statistical computation and QA evaluation of data retrieved from the
[seaicedata](https://bitbucket.org/nsidc/seaice/README/seaicedata.md) package
and write it to a daily or monthly datastore file as appropriate (via
[seaicedatastore](https://bitbucket.org/nsidc/seaice/README/seaicedatastore.md))
for use by other packages in the sea ice index project.

![sedna](https://bitbucket.org/nsidc/seaice/README/sedna.md)(doc/sedna.png)

# Usage

## CLI

This is a brief summary of the available CLI commands. For more information on
the available options for each command, use the `--help` flag.

* `update_sea_ice_statistics_daily` - updates the values in the daily datastore
  for a range of dates.

* `update_sea_ice_statistics_monthly` - updates the values in the monthly
  datastore for a range of dates.

* `initialize_sea_ice_statistics_daily` - builds a new daily datastore from
  available data and saves off the existing datastore if it exists. By default,
  the daily datastore is `/share/apps/seaice/datastore/daily.p`.

* `initialize_sea_ice_statistics_monthly` - builds a new monthly datastore from
  available data and saves off the existing datastore if it exists. By default,
  the monthly datastore is `/share/apps/seaice/datastore/monthly.p`.

* `validate_daily_data` - 'validates' data over a range appears to be good based
  on the options selected, and marks the QA field in the datastore
  appropriately.
