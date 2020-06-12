from os import sys

import click
import datetime
from subprocess import run

import seaice.nasateam as nt
import seaice.logging as seaicelogging

log = seaicelogging.init('seaice.tools')


def monthly_with_statistics(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.monthly_with_statistics'
    else:
        return 'monthly_with_statistics'


def sea_ice_extent_monthly_csvs(dev):
    if dev:
        return 'python -m seaice.tools.csvify.sea_ice_extent_monthly'
    else:
        return 'sea_ice_extent_monthly_csvs'


def regional_monthly(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.regional_monthly'
    else:
        return 'regional_monthly'


def monthly_by_year(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.monthly_by_year'
    else:
        return 'monthly_by_year'


def plot_monthly_ice_extent(dev):
    if dev:
        return 'python -m seaice.tools.plotter.monthly_extent'
    else:
        return 'plot_monthly_ice_extent'


def plot_monthly_ice_anomaly(dev):
    if dev:
        return 'python -m seaice.tools.plotter.monthly_anomaly'
    else:
        return 'plot_monthly_ice_anomaly'


def min_max_rankings(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.min_max_rankings'
    else:
        return 'min_max_rankings'


def rates_of_change(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.rates_of_change'
    else:
        return 'rates_of_change'


def monthly_extent_global(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.monthly_by_year_global'
    else:
        return 'monthly_by_year_global'


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False),
                default=nt.DATA_STORE_BASE_DIRECTORY)
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False),
                default='/share/apps/seaice/')
@click.option('--start_year', type=int, default=1981,
              help=('The start year for the climatology range.'))
@click.option('--end_year', type=int, default=2010,
              help=('The end year for the climatology range.'))
@click.option('--hires/--no-hires', is_flag=True, default=True,
              help=('Create high resolution versions of the monthly anomaly plots.'))
@click.option('--dev', is_flag=True, default=False,
              help=('Run commands with python -m, to run from source'))
@click.option('--dev', is_flag=True, default=False,
              help=('Run commands with python -m, to run from source'))
@seaicelogging.log_command(log)
def process_latest_monthly(input_directory, output_directory, start_year, end_year, hires, dev):
    """Run all monthly processing commands"""
    last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).month
    commands = [
        ('{} {} {}/xlsx').format(regional_monthly(dev),
                                 input_directory,
                                 output_directory),
        '{} -m {} -h N {}/monthly.p {}/plots'.format(plot_monthly_ice_anomaly(dev),
                                                     last_month,
                                                     input_directory,
                                                     output_directory),
        '{} -m {} -h S {}/monthly.p {}/plots'.format(plot_monthly_ice_anomaly(dev),
                                                     last_month,
                                                     input_directory,
                                                     output_directory),
        '{} -m {} -h N {}/monthly.p {}/plots'.format(plot_monthly_ice_extent(dev),
                                                     last_month,
                                                     input_directory,
                                                     output_directory),
        '{} -m {} -h S {}/monthly.p {}/plots'.format(plot_monthly_ice_extent(dev),
                                                     last_month,
                                                     input_directory,
                                                     output_directory),
        '{} {} {}/csv'.format(sea_ice_extent_monthly_csvs(dev), input_directory, output_directory),
        '{} {} {}/global'.format(monthly_extent_global(dev), input_directory, output_directory),
        '{} {} {}/xlsx'.format(monthly_by_year(dev), input_directory, output_directory),
        '{} {} {}/xlsx'.format(rates_of_change(dev), input_directory, output_directory),
        '{} {} {}/xlsx'.format(min_max_rankings(dev), input_directory, output_directory),
        '{} {} {}/xlsx'.format(monthly_with_statistics(dev), input_directory, output_directory)
    ]

    if hires:
        commands += [
            '{} --hires -m {} -h N {}/monthly.p {}/plots'.format(plot_monthly_ice_anomaly(dev),
                                                                 last_month,
                                                                 input_directory,
                                                                 output_directory),
            '{} --hires -m {} -h S {}/monthly.p {}/plots'.format(plot_monthly_ice_anomaly(dev),
                                                                 last_month,
                                                                 input_directory,
                                                                 output_directory)
        ]

        failures = [i.args for i in [_run_command(x) for x in commands] if i.returncode != 0]

        if failures:
            log.error('The following commands failed: {}'.format(failures))
            sys.exit(1)


def _run_command(cmd):
    print(cmd)
    return run(cmd, shell=True)


if __name__ == '__main__':
    process_latest_monthly()
