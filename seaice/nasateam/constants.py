"""Constants and utilities for working with nasateam sea ice data.

In a typical NSIDC deployment, these constants are overridden in an
`overrides.yaml` file living on the app network share.
"""

import datetime as dt
import logging
import os
import re
import sys

import pandas as pd
import yaml


log = logging.getLogger(__name__)

VERSION_STRING = 'v3.0'

VALID_HEMISPHERES = ['N', 'S']
NORTH_SHAPE = (448, 304)
SOUTH_SHAPE = (332, 316)

EXTENT_THRESHOLD = 15
SCALE = 2.5
VALID_DATA_RANGE = (0, 250)

MINIMUM_DAYS_FOR_VALID_MONTH = 20

BEGINNING_OF_SATELLITE_ERA = dt.date(1978, 10, 26)
BEGINNING_OF_SATELLITE_ERA_MONTHLY = dt.date(1978, 11, 1)
BEGINNING_OF_SATELLITE_ERA_YEARLY = dt.date(1979, 1, 1)

DEFAULT_CLIMATOLOGY_YEARS = (1981, 2010)

FLAGS = {
    'pole': 251,
    'unused': 252,
    'coast': 253,
    'land': 254,
    'missing': 255
}

# Preferred platform following V1.1 data convention.
PLATFORM_RANGES = {
    'n07': [('1978-10-25', '1987-08-20')],
    'f08': [('1987-08-21', '1991-12-18')],
    'f11': [('1991-12-19', '1995-09-29')],
    'f13': [('1995-09-30', '2007-12-31')],
    'f17': [('2008-01-01', '2018-12-31')],
    'f18': [('2019-01-01', '2250-01-01')]
}

LAST_DAY_WITH_VALID_FINAL_DATA = dt.date(2018, 12, 31)

DEFAULT_FINAL_SEA_ICE_PATHS = ['/media/apbarret/My\ Passport/Data/seaice/nsidc-0051/']
DEFAULT_NRT_SEA_ICE_PATHS = ['/media/apbarret/My\ Passport/Data/seaice/nsidc-0081/']
DEFAULT_SEA_ICE_PATHS = [*DEFAULT_FINAL_SEA_ICE_PATHS, *DEFAULT_NRT_SEA_ICE_PATHS]


DATA_FILENAME_MATCHER = re.compile(
    '(?P<filename>.*nt_{date}_{platform}_{version}_{hemi}\.bin)'.format(
        date='(?P<date>(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})?)',
        platform='(?P<platform>[nf]\d{2})',
        version='(?P<version>nrt|v01|v1\.1)',
        hemi='(?P<hemisphere>n|s)'
    )
)

SMMR_PLATFORM = 'n07'

start, end = PLATFORM_RANGES[SMMR_PLATFORM][0]
SMMR_DAYS = pd.period_range(start=start, end=end, freq='D')[1::2]

DAILY_DEFAULT_COLUMNS = ['total_extent_km2',
                         'total_area_km2',
                         'missing_km2',
                         'hemisphere',
                         'filename',
                         'source_dataset',
                         'failed_qa']

MONTHLY_DEFAULT_COLUMNS = DAILY_DEFAULT_COLUMNS.copy()
MONTHLY_DEFAULT_COLUMNS.remove('failed_qa')


METADATA_COLUMNS = DAILY_DEFAULT_COLUMNS[3:]


SEA_ICE_BASE_DIR = '/share/apps/seaice/'


# A lot of code in the sea ice index depends on these constants and we never
# made it easy to modify.  This is somewhat circuitious, but allows a user to
# create a simple yaml file to override variables in this constants.py by
# setting an environment variable to the filename.

if 'OVERRIDE_NASATEAM_CONSTANTS' in os.environ:
    override_yaml = yaml.load(open(os.environ['OVERRIDE_NASATEAM_CONSTANTS'], 'r'))
    this_module = sys.modules[__name__]
    for name, value in override_yaml.items():
        log.info('overriding nasateam constant:{}:{}=>{}'.format(
            name, getattr(this_module, name), value))
        setattr(this_module, name, value)

SEASONS = {
    'spring': (3, 4, 5),
    'summer': (6, 7, 8),
    'autumn': (9, 10, 11),
    'winter': (12, 1, 2)
}
