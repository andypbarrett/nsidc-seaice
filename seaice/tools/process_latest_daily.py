from os import sys

import click
from subprocess import run

import seaice.nasateam as nt
import seaice.logging as seaicelogging

log = seaicelogging.init('seaice.tools')


def regional_daily(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.regional_daily'
    else:
        return 'regional_daily'


def plot_daily_ice_extent(dev):
    if dev:
        return 'python -m seaice.tools.plotter.daily_extent'
    else:
        return 'plot_daily_ice_extent'


def sea_ice_climatology_csvs(dev):
    if dev:
        return 'python -m seaice.tools.csvify.sea_ice_climatology'
    else:
        return 'sea_ice_climatology_csvs'


def daily_extent(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.daily_extent'
    else:
        return 'daily_extent'


def daily_extent_global(dev):
    if dev:
        return 'python -m seaice.tools.xlsify.daily_extent_global'
    else:
        return 'daily_extent_global'


def sea_ice_extent_daily_csvs(dev):
    if dev:
        return 'python -m seaice.tools.csvify.sea_ice_extent_daily'
    else:
        return 'sea_ice_extent_daily_csvs'


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False),
                default=nt.DATA_STORE_BASE_DIRECTORY)
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False),
                default='/share/apps/seaice')
@click.option('--start_year', type=int, default=1981,
              help=('The start year for the climatology range.'))
@click.option('--end_year', type=int, default=2010,
              help=('The end year for the climatology range.'))
@click.option('--dev', is_flag=True, default=False,
              help=('Run commands with python -m, to run from source'))
@seaicelogging.log_command(log)
def process_latest_daily(input_directory, output_directory, start_year, end_year, dev):
    """Run all daily processing commands"""
    commands = [
        '{} {} {}/xlsx/'.format(regional_daily(dev), input_directory, output_directory),
        '{} {} {}/csv'.format(sea_ice_extent_daily_csvs(dev), input_directory, output_directory),
        '{} {} {}/xlsx'.format(daily_extent(dev), input_directory, output_directory),
        '{} {} {}/global'.format(daily_extent_global(dev), input_directory, output_directory),
        '{} --standard_plot=north --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                output_directory),
        '{} --standard_plot=south --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                output_directory),
        '{} --standard_plot=asina_north --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                      output_directory),
        '{} --standard_plot=asina_south --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                      output_directory),
        '{} --standard_plot=north_iqr --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                    output_directory),
        '{} --standard_plot=south_iqr --output_dir {}/plots'.format(plot_daily_ice_extent(dev),
                                                                    output_directory),
        ('{} --standard_plot=asina_north_iqr '
         '--output_dir {}/plots').format(plot_daily_ice_extent(dev), output_directory),
        '{} --standard_plot=asina_south_iqr --output_dir {}/plots'.format(
            plot_daily_ice_extent(dev),
            output_directory
        )
    ]

    failures = [i.args for i in [_run_command(x) for x in commands] if i.returncode != 0]

    if failures:
        log.error('The following commands failed: {}'.format(failures))
        sys.exit(1)


def _run_command(cmd):
    print(cmd)
    return run(cmd, shell=True)


if __name__ == '__main__':
    process_latest_daily()
