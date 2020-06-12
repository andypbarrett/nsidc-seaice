nasateam
---

**nasateam** contains constants and metadata necessary for reading and
understanding datasets that are used in the production of the sea ice index,
such as [NSIDC-0051](https://nsidc.org/data/nsidc-0051),
[NSIDC-0081](https://nsidc.org/data/nsidc-0081), and
[NSIDC-0622](https://nsidc.org/data/nsidc-0622).  Most of the sofware packages
to create files for the [Sea Ice Index][sii] require this package.

# Usage

## In other Python modules

```
#!python
import seaice.nasateam as nt
```


## To Customize Constants

Create a yaml file (like `override.yaml`) with desired constants, and set the
envrionment variable `OVERRIDE_NASATEAM_CONSTANTS` to the full path to
`override.yaml`. (Do be careful with `DEFAULT_FINAL_SEA_ICE_PATHS`,
`DEFAULT_NRT_SEA_ICE_PATHS` if you change these you will probably also want to
include `DEFAULT_SEA_ICE_PATHS` as it's normally created from the combination of
the previous values.)

Values set in `override.yaml` will override the values set in `constants.py`
(so nasateam values that are set in other modules, like `hemispheres.py`, cannot
be overridden using this method).

Example:

```
#!yaml
# override.yaml
DEFAULT_FINAL_SEA_ICE_PATHS:
  - '/some/path/for/testing/'

DEFAULT_NRT_SEA_ICE_PATHS:
  - '/projects/DATASETS/nsidc0081_nrt_nasateam_seaice'

DEFAULT_SEA_ICE_PATHS:
  - '/some/path/for/testing/'
  - '/projects/DATASETS/nsidc0081_nrt_nasateam_seaice'

PLATFORM_RANGES:
  n07: !!python/tuple ['1978-10-25', '1987-08-20']
  f08: !!python/tuple ['1987-08-21', '1991-12-18']
  f11: !!python/tuple ['1991-12-19', '1995-09-29']
  f13: !!python/tuple ['1995-09-30', '2007-12-31']
  f17: !!python/tuple ['2008-01-01', '2016-03-31']
  f18: !!python/tuple ['2016-04-01', '2250-01-01']
```

The types of values that can be overridden are limited by the yaml parser;
numbers, strings, dates (e.g., a value of `2017-08-10`, with no quotes will be
parsed by pyyaml as a `datetime.date`), etc.; so `DATA_FILENAME_MATCHER` should
not be set in `override.yaml`, since it is a regex object.
