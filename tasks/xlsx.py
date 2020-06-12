from invoke import run, task

from . import dirs


def regional_daily_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.regional_daily'
    else:
        cmd = 'regional_daily'

    return cmd


def regional_monthly_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.regional_monthly'
    else:
        cmd = 'regional_monthly'

    return cmd


def daily_extent_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.daily_extent'
    else:
        cmd = 'daily_extent'

    return cmd


def min_max_rankings_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.min_max_rankings'
    else:
        cmd = 'min_max_rankings'

    return cmd


def monthly_with_statistics_cmd(mode):

    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.monthly_with_statistics'
    else:
        cmd = 'monthly_with_statistics'

    return cmd


def trend_cmd(mode):

    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.rates_of_change'
    else:
        cmd = 'rates_of_change'

    return cmd


def monthly_by_year_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.xlsify.monthly_by_year'
    else:
        cmd = 'monthly_by_year'

    return cmd


@task
def regional_daily(ctx, mode='development',
                   input_dir=dirs.datastore_directory(),
                   output_dir=dirs.output_dir()):
    """ process daily.p datastore into regional analysis excel file """

    run('mkdir -p {0}'.format(output_dir))
    cmd = '{cmd} {input_dir} {output_dir}'.format(
        cmd=regional_daily_cmd(mode),
        input_dir=input_dir,
        output_dir=output_dir)
    run(cmd, pty=True)


@task
def regional_monthly(ctx, mode='development',
                     input_dir=dirs.datastore_directory(),
                     output_dir=dirs.output_dir()):
    """process monthly.p datastore into regional analysis excel file:
    Sea_Ice_Index_Regional_Monthly_Data_G02135_v3.0.xlsx

    """

    run('mkdir -p {0}'.format(output_dir))
    cmd = '{cmd} {input_dir} {output_dir}'.format(
        cmd=regional_monthly_cmd(mode),
        input_dir=input_dir,
        output_dir=output_dir)
    run(cmd, pty=True)


@task
def daily_extent(ctx, mode='development', output_dir=dirs.output_dir()):
    """
    compute daily sea ice statistics Sea_Ice_Index_Daily_Extent_G02135_v3.0.xlsx
    """
    run('mkdir -p {0}'.format(output_dir))
    cmd = '{cmd} {data_dir} {output_dir}'.format(
        cmd=daily_extent_cmd(mode),
        data_dir=dirs.datastore_directory(),
        output_dir=output_dir)
    run(cmd, pty=True)


@task
def minmax(ctx, mode='development', output_dir=dirs.output_dir()):
    """compute min/max monthly/daily trends in sea ice extent
    Sea_Ice_Min_Max_Rankings_G02135_v3.0.xlsx

    """
    run('mkdir -p {0}'.format(output_dir))
    cmd = '{minmax} {data_dir} {output_dir}'.format(
        minmax=min_max_rankings_cmd(mode),
        data_dir=dirs.datastore_directory(),
        output_dir=output_dir)
    run(cmd, pty=True)


@task
def monthly_sea_ice_with_statistics(ctx, mode='development', output_dir=dirs.output_dir()):
    """
    Generate monthly XLS file: Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_v3.0.xlsx.
    """
    run('mkdir -p {0}'.format(output_dir))
    cmd = '{monthly_with_statistics} {data_dir} {output_dir}'.format(
        monthly_with_statistics=monthly_with_statistics_cmd(mode),
        data_dir=dirs.datastore_directory(),
        output_dir=output_dir)
    run(cmd, pty=True)


@task
def rates_of_change(ctx, mode='development', output_dir=dirs.output_dir()):
    """
    Generate monthly/daily trends in ice extent: Sea_Ice_Index_Rates_of_Change_G02135_v3.0.xlsx
    """
    run('mkdir -p {0}'.format(output_dir))
    cmd = '{trend} {data_dir} {output_dir}'.format(
          trend=trend_cmd(mode),
          data_dir=dirs.datastore_directory(),
          output_dir=output_dir)
    run(cmd, pty=True)


@task
def monthly_sea_ice_by_year(ctx, mode='development', output_dir=dirs.output_dir()):
    """
    Generate XLSX file with monthly values arranged with a different year in
    each row and a different month in each
    column. Sea_Ice_Index_Monthly_Data_by_Year_G02135_v3.0.xlsx
    """
    run('mkdir -p {0}'.format(output_dir))
    cmd = '{monthly_by_year} {data_dir} {output_dir}'.format(
        monthly_by_year=monthly_by_year_cmd(mode),
        data_dir=dirs.datastore_directory(),
        output_dir=output_dir)
    run(cmd, pty=True)


@task(default=True)
def all(ctx, mode='development', output_root_dir=None):
    """
    All xlsx files: Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_v3.0.xlsx,
    Sea_Ice_Index_Min_Max_Rankings_G02135_v3.0.xlsx,
    Sea_Ice_Index_Daily_Extent_G02135_v3.0.xlsx,
    Sea_Ice_Index_Regional_Monthly_Data_G02135_v3.0.xlsx,
    Sea_Ice_Index_Regional_Daily_Data_G02135_v3.0.xlsx
    """
    if output_root_dir is None:
        output_root_dir = dirs.output_dir()

    monthly_sea_ice_with_statistics(ctx, mode, output_dir=output_root_dir)
    minmax(ctx, mode, output_dir=output_root_dir)
    daily_extent(ctx, mode, output_dir=output_root_dir)
    rates_of_change(ctx, mode, output_dir=output_root_dir)
    regional_monthly(ctx, mode, output_dir=output_root_dir)
    regional_daily(ctx, mode, output_dir=output_root_dir)
    monthly_sea_ice_by_year(ctx, mode, output_dir=output_root_dir)
