seaicedata
---

**seaicedata** provides an API for retrieving various (e.g. concentration,
extent) gridsets built from [NSIDC-0051](https://nsidc.org/data/nsidc-0051) and
[NSIDC-0081](https://nsidc.org/data/nsidc-0081) data.

![seaicedata](doc/seaicedata.png)

# Requirements

A directory containing the binary data files from nsidc-0051 and nsidc-0081
needs to be mounted to use this package. The path to the directory can then
be used as the `search_paths` argument with the package's API functions. If
no argument is used, the package assumes the datasets are mounted at
`/projects/DATASETS/nsidc0051_gsfc_nasateam_seaice` and
`/projects/DATASETS/nsidc0081_nrt_nasateam_seaice`.

# Usage

## In other Python modules

```
#!python
import seaice.data as sid
```

## Example usage
```
# get daily concentration for Sept 16th, 2012
daily = sid.concentration_daily(nt.NORTH, 2012, 9, 16)

# daily with any missing data filled in by averaging surrounding days
daily = sid.concentration_daily(nt.NORTH, 2012, 9, 16, interpolation_radius=1)

# get monthly concentration for september 2012
monthly = sid.concentration_monthly(nt.NORTH, 2012, 9)

# view documentation for all api functions
help(sid)
```

## CLI

```
monthly_files_from_dailies --help
```
