import click
import os

from .. import api
from seaice import version_flag
from . import cli_util as util
import seaice.nasateam as nt
import seaice.logging as seaicelogging


log = seaicelogging.init('seaice.images')


@click.command()
@version_flag
@click.option('-o', '--output', default=os.path.join(nt.SEA_ICE_BASE_DIR, 'googleearth'),
              help='Output image filename or directory.')
@click.option('-c', '--config_filename', default=None,
              help='Alternative configuration yaml file.  Must have all necessary options.')
@click.option('--allow-bad-data', is_flag=True, default=False,
              help='Ignore any errors in source data and create an image')
@click.option('--latest', type=int,
              help='Creates the INTEGER latest available images. Not compatible '
              'with --year, --month.')
@click.option('--all', is_flag=True, default=False,
              help='Creates images for all dates since {}.'
              ' Not compatible with --year or --latest. If used with -m, the list of dates '
              'will be filtered based on those options. For example, \'--all -m 9\' would '
              'select all September dates.'
              '--latest'.format(nt.BEGINNING_OF_SATELLITE_ERA.strftime('%Y-%m-%d')))
@click.option('--range', type=util.DateRange, default=None,
              help='Creates images two dates. Dates should be formatted as YYYYMMDD '
              'and separated by a comma (e.g., 20101201,20111201). Not compatible '
              'with --year, --month, --latest.')
@click.option('-y', '--year', type=int, help=('YYYY. Year.'))
@click.option('-m', '--month', type=int, help=('MM. Month.'))
@click.option('--overwrite/--no-overwrite', default=True,
              help='Overwrite existing images. --no-overwrite can be used to '
              'skip image generation if the target output image is already '
              'found to save time.')
@seaicelogging.log_command(log)
def sii_image_google_earth(**config):
    """sii_image_google_earth is a command line interface interface to create images
    for displaying monthly sea ice extent in Google Earth.

    Usage examples:

    \b
    * Generate a single monthly extent image in the current directory.

       sii_image_google_earth -y 2016 -m 9 -o .

    \b
    * Generate images for all Septembers in the satellite record, placing them
      in a directory Sep/

       sii_image_google_earth --all -m 9 -o Sep/

    """
    config['google'] = True
    config['temporality'] = 'monthly'
    config = util.validate_command_line_options(config)
    dates = util.get_dates(config)

    count = len(dates)
    log.info('Creating {count} image{s}...'.format(count=count,
                                                   s='' if count == 1 else 's'))

    for date in dates:
        api.google_earth_image(date,
                               temporality=config['temporality'],
                               image_type='extent',
                               output=config['output'],
                               config_filename=config['config_filename'],
                               allow_bad_data=config['allow_bad_data'],
                               overwrite=config['overwrite'])


if __name__ == '__main__':
    sii_image_google_earth()
