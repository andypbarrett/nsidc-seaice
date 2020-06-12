import os

from invoke import task, run

from . import dirs


def climatology_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.csvify.sea_ice_climatology'
    else:
        cmd = 'sea_ice_climatology'

    return cmd


def sea_ice_extent_csvs_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.csvify.sea_ice_extent_daily'
    else:
        cmd = 'sea_ice_daily_csvs'

    return cmd


def sea_ice_monthly_csvs_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.tools.csvify.sea_ice_extent_monthly'
    else:
        cmd = 'sea_ice_monthly_csvs'

    return cmd


@task
def monthly_csvs(ctx, mode='development', output_root_dir=None, datastore_dir=None):
    """
    Generate monthly CSV files with area and extent for every month.
    """
    if output_root_dir is None:
        output_root_dir = os.path.join(dirs.output_dir(), 'monthly_csv')

    if datastore_dir is None:
        datastore_dir = dirs.datastore_directory()
    os.makedirs(output_root_dir, exist_ok=True)

    cmd = '{cmd} {data_dir} {output_dir}'.format(
            cmd=sea_ice_monthly_csvs_cmd(mode),
            data_dir=datastore_dir,
            output_dir=output_root_dir)
    print(cmd)
    run(cmd)


@task
def climatology_csvs(ctx, mode='development', output_root_dir=None):
    """
    Generate statistics (mean, stddev, quantiles for the climatological period
   """
    if output_root_dir is None:
        output_root_dir = dirs.output_dir()
    os.makedirs(output_root_dir, exist_ok=True)

    cmd = '{cmd} --output_directory={output_dir}'.format(cmd=climatology_cmd(mode),
                                                         output_dir=output_root_dir)
    print(cmd)
    run(cmd)


@task
def daily_csvs(ctx, mode='development', output_root_dir=None, datastore_dir=None):
    """
    Generate daily seaice_extent csvs with extent and missing for every day from sedna
    output.
    """
    if output_root_dir is None:
        output_root_dir = dirs.output_dir()
    os.makedirs(output_root_dir, exist_ok=True)

    if datastore_dir is None:
        datastore_dir = dirs.datastore_directory()

    cmd = '{cmd} {data_dir} {out_root}'.format(cmd=sea_ice_extent_csvs_cmd(mode),
                                               data_dir=datastore_dir,
                                               out_root=output_root_dir)
    print(cmd)
    run(cmd)


@task(default=True)
def all(ctx, mode='development', output_root_dir=None):
    """
    Generate all csv files: daily N&S nrt/final/joint & sea_ice_extent_climatogy csvs
    """
    monthly_csvs(ctx, mode, output_root_dir)
    daily_csvs(ctx, mode, output_root_dir)
    climatology_csvs(ctx, mode, output_root_dir)
