from functools import lru_cache

import seaice.nasateam as nt
from . import seaicedatastore


def write_daily_datastore(dataframe=None, columns=None,
                          data_store=nt.DAILY_DATA_STORE_FILENAME):
    """Writes a daily data store when given a datastore dataframe,
       data_store location, list of columns and defined frequency.

       Keyword arguments:
       ------------
       dataframe            -- A seaice data store dataframe
       columns              -- List of writeable columns in the dataframe
       data_store           -- Location to write the data store.  Defaults
                               to the nasateam default daily datastore
    """
    seaicedatastore.write_datastore(dataframe, data_store, columns)


def write_monthly_datastore(dataframe=None, columns=None,
                            data_store=nt.MONTHLY_DATA_STORE_FILENAME):
    """Writes a monthly data store when given a datastore dataframe,
       data_store location, list of columns and defined frequency.

       Keyword arguments:
       ------------
       dataframe            -- A seaice data store dataframe
       columns              -- List of writeable columns in the dataframe
       data_store           -- Location to write the data store.  Defaults to
                               the nasateam default monthly datastore
    """
    seaicedatastore.write_datastore(dataframe, data_store, columns)


def new_daily_dataframe():
    """Returns an empty daily dataframe with default data store columns/indices."""
    return seaicedatastore.new_dataframe('D')


def new_monthly_dataframe():
    """Returns an empty monthly dataframe with default data store columns/indices."""
    return seaicedatastore.new_dataframe('M')


def daily_dataframe(data_store=nt.DAILY_DATA_STORE_FILENAME):
    """Returns a dataframe representing a daily seaice data store

        Keyword arguments:
        ------------
        data_store          -- Location of the data store.  Defaults to use the
                               nasateam defined default daily data store location.

    """
    df = seaicedatastore.read_datastore(data_store)

    return df


def monthly_dataframe(data_store=nt.MONTHLY_DATA_STORE_FILENAME):
    """Returns a dataframe representing a monthly seaice data store

        Keyword arguments:
        ------------
        data_store          -- Location of the data store.  Defaults to use the
                               nasateam defined default monthly data store location.
    """
    return seaicedatastore.read_datastore(data_store)


@lru_cache()
def get_bad_days_for_hemisphere(hemisphere, data_store=nt.DAILY_DATA_STORE_FILENAME):
    """Returns a list of pandas daily periods representing days that were marked as 'bad'
       in the QA field in the daily data store.

       Keyword arguments:
       ------------
       hemisphere           -- Hemisphere to query for bad days  "N" or "S"
       data_store           -- Daily data store location.   Defaults to nasateam
                               defined default daily data store location
    """
    return seaicedatastore.get_bad_days_for_hemisphere(hemisphere, data_store)
