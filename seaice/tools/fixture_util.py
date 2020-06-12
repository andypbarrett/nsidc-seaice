import seaice.datastore as sds
from seaice.datastore import fixture


def create_fixture(csv_source, fixture_target, periodicity):
    """Create test pickled fixture from .csv"""
    if periodicity == 'D':
        df = fixture.from_daily_csv(csv_source)
        sds.write_daily_datastore(dataframe=df, data_store=fixture_target)

    elif periodicity == 'M':
        df = fixture.from_monthly_csv(csv_source)
        sds.write_monthly_datastore(dataframe=df, data_store=fixture_target)
