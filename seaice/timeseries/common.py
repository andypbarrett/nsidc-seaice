"""seaicetimeseries package constants"""

import datetime as dt

import seaice.nasateam as nt


class SeaIceTimeseriesException(Exception):
    pass


class SeaIceTimeseriesInvalidArgument(ValueError):
    pass


# For nday averages (5 day averages)
NUM_DAYS = 5
MIN_VALID_DAYS = 2


DEFAULT_CLIMATOLOGY_DATES = [dt.date(nt.DEFAULT_CLIMATOLOGY_YEARS[0], 1, 1),
                             dt.date(nt.DEFAULT_CLIMATOLOGY_YEARS[1], 12, 31)]

DEFAULT_QUANTILES = [.25, .5, .75]

# square kilometers to square miles
KM2_TO_MI2 = 0.386102
