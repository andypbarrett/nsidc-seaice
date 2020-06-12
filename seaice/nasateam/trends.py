import datetime as dt
from functools import lru_cache

import pandas as pd

from .constants import BEGINNING_OF_SATELLITE_ERA_MONTHLY
from .errors import SeaIceBadSeason


@lru_cache(maxsize=4)
def datetime_index_for_seasonal_trends(year, months):
    """Returns a DatetimeIndex containing every day in the satellite era in the
    given season (or months) through the given year. Only dates in complete
    seasons are returned.

    year: integer for the year through which you want to find the seasonl trend

    months: tuple of consecutive months (integers) defining the season

    """
    first_of_current_month = dt.date.today().replace(day=1)
    last_day_of_previous_month = first_of_current_month - dt.timedelta(1)

    # start with all the days for all complete months
    dates = pd.date_range(start=BEGINNING_OF_SATELLITE_ERA_MONTHLY,
                          end=last_day_of_previous_month)

    # cut off at the given year
    dates = dates[dates.year <= year]

    # cut off any days that are in incomplete seasons
    first_day_of_season = dates[dates.month == months[0]][0]
    last_day_of_season = dates[dates.month == months[-1]][-1]
    dates = dates[(first_day_of_season <= dates) & (dates <= last_day_of_season)]

    # pick out just the dates in the given months
    seasonal_dates = pd.DatetimeIndex([])
    for month in months:
        seasonal_dates = seasonal_dates.union(dates[dates.month == month])

    return seasonal_dates


def validate_seasons(seasons):
    for season, months in seasons.items():
        if len(months) != 3:
            raise SeaIceBadSeason('season definition for "{}" should '
                                  'have 3 months, but has {}'.format(season, months))

        for i in range(len(months) - 1):
            this_month = months[i]
            expected_next_month = 1 if this_month == 12 else this_month + 1

            if months[i + 1] != expected_next_month:
                raise SeaIceBadSeason('season definition for "{}" has '
                                      'nonconsecutive months: {}'.format(season, months))
