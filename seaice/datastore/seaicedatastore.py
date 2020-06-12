import logging

import numpy as np
import pandas as pd

import seaice.nasateam as nt

log = logging.getLogger(__name__)


def write_datastore(df, data_store, columns=None):
    """Given a seaicedatastore dataframe, data store location and list of columns
       to write, serialize and write to disk"""
    if columns is None:
        columns = df.columns
    if 'hemisphere' in columns:
        columns.remove('hemisphere')
    df = df.sort_index()
    df[columns].to_pickle(data_store)
    log.info('saved data store: {}'.format(data_store))


def new_dataframe(frequency):
    if frequency not in ['D', 'M']:
        raise SeaicedatastoreError('Could not initialize'
                                   ' database with frequency {}'.format(frequency))

    df = pd.DataFrame(index=pd.PeriodIndex([], freq=frequency, name=index_label(frequency)),
                      columns=_column_names(frequency))
    df = df.set_index([df.index, 'hemisphere'])
    return df


def read_datastore(data_store):
    try:
        return pd.read_pickle(data_store)
    except OSError as e:
        raise SeaicedatastoreDataStoreNotFoundError(str(e))


def get_bad_days_for_hemisphere(hemisphere, data_store):
    """Returns a list of Periods representing bad days given a hemisphere and data_store location"""
    frame = read_datastore(data_store)
    if hemisphere not in frame.index.get_level_values('hemisphere').unique():
        return []
    hemi_frame = frame.xs(hemisphere, level='hemisphere')

    try:
        failed_qa_series = hemi_frame['failed_qa'].replace(np.nan, False)
        return hemi_frame[failed_qa_series].index.tolist()
    except KeyError:
        log.warning('failed_qa column not found for %s %s', hemisphere, data_store)
        return []


def index_label(frequency):
    """Returns appropriate mapping from frequency to index column name"""
    return {'D': 'date',
            'M': 'month'}[frequency]


def _column_names(frequency):
    return {'D': nt.DAILY_DEFAULT_COLUMNS,
            'M': nt.MONTHLY_DEFAULT_COLUMNS}[frequency]


class SeaicedatastoreError(Exception):
    pass


class SeaicedatastoreDataStoreNotFoundError(Exception):
    def __init__(self, message):
        Exception.__init__(self, 'Datastore could not be opened due to file'
                           'system error: {}'.format(message))
