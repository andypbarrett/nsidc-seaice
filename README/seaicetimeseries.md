seaicetimeseries
----------------

**seaicetimeseries** provides an API for accessing time series data from the
[seaicedatastore][bitbucket-seaicedatastore](https://bitbucket.org/nsidc/seaice/README/seaicedatastore.md).

![seaicetimeseries](doc/seaicetimeseries.png)

# Usage

## In other Python modules

```
#!python
import seaice.timeseries as sit

# Return a pandas dataframe of the data in the daily datastore
# filtered by input parameters
daily_ts = sit.daily(hemisphere='N')

# Monthly dataframe
monthly_ts = sit.monthly(hemisphere='N')
```

See the docstrings in `api.py`, or use `help(sit)` to learn about the full
list of available API functions and optional arguments.
