""" Access the data_store and return raw dataframes """

import seaice.datastore as sds


def _dataframe_from_data_store(data_store):
    """Read dataframe from CSV file or return a new empty dataframe.

    We set the index to be a multiindex of date + hemisphere in order to have
    unique values because sea ice statistics exist in both hemispheres.

    """
    try:
        df = sds.daily_dataframe(data_store)
        return df
    # data_store file does not exist
    except sds.seaicedatastore.SeaicedatastoreDataStoreNotFoundError:
        return sds.new_daily_dataframe()


def _dataframe_from_data_store_monthly(data_store):
    try:
        df = sds.monthly_dataframe(data_store)
        return df
    # data_store file does not exist
    except sds.seaicedatastore.SeaicedatastoreDataStoreNotFoundError:
        return sds.new_monthly_dataframe()
