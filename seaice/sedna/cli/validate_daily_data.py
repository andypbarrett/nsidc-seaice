import copy
import sys

import click
import pandas as pd

from .. import sedna
from seaice import version_flag
from .util import DAILY_STATISTICS_DEFAULT_CONFIG
from .util import load_config
from .util import options
import seaice.nasateam as nt
import seaice.logging as sil

log = sil.init('seaice.sedna')


@click.command()
@version_flag
@options(['daily', 'base', 'regression'])
@click.option('-w', '--write_bad_days',
              type=bool,
              default=False,
              help='Set command to write to bad days inventory file')
@sil.log_command(log)
def validate_daily_data(hemisphere, start_date, end_date, configfile, write_bad_days,
                        eval_days, regression_delta_km2):
    """Given a range of dates and a hemisphere, validate data for unusual changes
    in seaice extent.   When an extent delta exceeds a threshold value,
    list the date and optionally add that date to a bad data list
    """
    _validate_daily_data(hemisphere, start_date, end_date, configfile, write_bad_days,
                         eval_days, regression_delta_km2)


def _validate_daily_data(hemisphere=None, start_date=None, end_date=None, configfile=None,
                         write_bad_days=None, eval_days=None, regression_delta_km2=None):

    dates = pd.period_range(start_date, end_date)
    config = copy.deepcopy(DAILY_STATISTICS_DEFAULT_CONFIG)
    config.update(load_config(configfile))
    hemisphere = nt.by_name(hemisphere)['short_name']
    data_store = config.get('data_store', 'daily.p')
    validation_frame = sedna.get_validation_frame(dates, data_store,
                                                  hemisphere, regression_delta_km2, eval_days)
    validation_frame = validation_frame.dropna()
    failure_series = validation_frame[validation_frame['failed_qa']]['failed_qa']
    if len(failure_series) > 0:
        log.warn('The following dates failed validation:' +
                 str([str(x[0]) for x in failure_series.index.tolist()]))
        if write_bad_days:
            sedna.merge_daily_datastore_with_validation_dataframe(validation_frame, data_store)
            log.warn('The dates have been flagged in the sedna datastore ({})'.format(data_store))
        sys.exit(1)
    log.info('validate_daily_data completed with no errors')


if __name__ == '__main__':
    validate_daily_data()
