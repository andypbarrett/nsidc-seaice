import json

import pandas as pd

from .seaicedatastore import SeaicedatastoreDataStoreNotFoundError, index_label


def from_daily_csv(data_store):
    """Return a seaicedatastore dataframe from a datastore formatted csv flie

      Format:

      date, hemisphere, filename, data_column1, data_column2
      1980-01-01, {N,S}, "['foo', 'bar']", 0.0, 0.0

      Will return a multiindex (date, hemisphere) datastore dataframe  with the filelist converted
      to a list.
    """
    index_name = index_label('D')
    df = _read_csv(data_store)
    df = df.set_index(pd.to_datetime(df[index_name].values).to_period('D'))
    df.index.name = index_name
    df = df.drop(index_name, axis=1)
    df.hemisphere = df.hemisphere.apply(str.capitalize)
    df = df.set_index([df.index, 'hemisphere'])
    df = _parse_filename_list(df)
    return df


def from_monthly_csv(data_store):
    """Return a seaicedatastore dataframe from a datastore formatted csv flie

      Format:

      month, hemisphere, filename, data_column1, data_column2
      1980-01-01, {N,S}, "['foo', 'bar']", 0.0, 0.0

      Will return a multiindex (date, hemisphere) datastore dataframe with the filelist converted
      to a list.
    """
    index_name = index_label('M')
    df = _read_csv(data_store)
    df = df.set_index(pd.to_datetime(df[index_name].values + '-01').to_period('M'))
    df.index.name = index_name
    df = df.drop(index_name, axis=1)
    df.hemisphere = df.hemisphere.apply(str.capitalize)
    df = df.set_index([df.index, 'hemisphere'])
    df = _parse_filename_list(df)
    return df


def _parse_filename_list(df_in):
    df = df_in.copy()

    # filename values are strings that look like this:
    #     ['/file/name', '/another/file/name']
    # JSON requires double quotes, and using the JSON parser transforms the
    # values into proper lists of strings
    df.filename = df.filename.apply(lambda x: json.loads(x.replace('\'', '"')))

    return df


def _read_csv(data_store):
    try:
        return pd.read_csv(data_store, low_memory=False)
    except OSError as e:
        raise SeaicedatastoreDataStoreNotFoundError(str(e))
