from invoke import run, task


def init_daily_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.sedna.cli.initialize_sea_ice_statistics_daily'
    else:
        cmd = 'initialize_sea_ice_statistics_daily'

    return cmd


def monthly_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.sedna.cli.sea_ice_statistics_monthly'
    else:
        cmd = 'sea_ice_statistics_monthly'

    return cmd


@task
def initialize_sea_ice_statistics_daily(ctx, mode='development'):
    """Generate daily.p datastore."""
    run(init_daily_cmd(mode), pty=True)


@task
def sea_ice_statistics_monthly(ctx, mode='development'):
    """Generate monthly.p datastore."""
    run(monthly_cmd(mode), pty=True)
