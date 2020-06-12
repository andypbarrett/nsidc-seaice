from itertools import product

import click

from .. import api
from seaice import version_flag
from . import cli_util as util
from ..errors import SeaIceImagesNoData
from .year_range import YearRange
import seaice.nasateam as nt
import seaice.logging as seaicelogging


log = seaicelogging.init('seaice.images')


@click.command()
@version_flag
# optional options
@click.option('-o', '--output', default=None,
              help='Output image filename or directory.')
@click.option('-c', '--config_filename', default=None,
              help='Alternative configuration yaml file.  Must have all necessary options.')
@click.option('--allow-bad-data', is_flag=True, default=False,
              help='Ignore any errors in source data and create an image')
@click.option('--latest', type=int,
              help='Creates the INTEGER latest available images. Not compatible '
              'with -y, -m, -d, --range')
@click.option('-f', '--flatten', is_flag=True, default=False,
              help='Create the GeoTiff images without the archive directory structure.')
@click.option('--all', is_flag=True, default=False,
              help='Creates GeoTiffs of the selected type for all dates since {}.'
              ' If used with -y, -m, or -d, the list of dates will be filtered '
              'based on those options. For example, \'--all -m 9\' would select '
              'all September dates. Not compatible with --latest, '
              '--range'.format(nt.BEGINNING_OF_SATELLITE_ERA.isoformat()))
@click.option('--range', type=util.DateRange, default=None,
              help='Creates GeoTiffs of the selected type and temporailty between two dates.'
              ' Dates should be formatted as YYYYMMDD and separated by a comma (e.g.,'
              ' 20101201,20111201). Not compatible with -y, -m, -d, --latest')
@click.option('--overwrite/--no-overwrite', default=True,
              help='Overwrite existing GeoTiff images. --no-overwrite can be used to '
              'skip image generation if the target output image is already '
              'found to save time.')
# feature switches
@click.option('--daily', 'temporality', flag_value='daily', default=True,
              help='(temporality) Create daily GeoTiff image.')
@click.option('--monthly', 'temporality', flag_value='monthly',
              help='(temporality) Create monthly GeoTiff image.')
@click.option('--concentration', 'image_type', flag_value='concentration', default=True,
              help='(image_type) Create concentration GeoTiff.')
@click.option('--extent', 'image_type', flag_value='extent',
              help='(image_type) Create extent GeoTiff.')
@click.option('--anomaly', 'image_type', flag_value='anomaly',
              help='(image_type) Create anomaly GeoTiff.')
@click.option('--trend', 'image_type', flag_value='trend',
              help='(image_type) Create trend GeoTiff.')
# Optional for Trend images.
@click.option('--trend-clip', default=100, help='Clip all trends values exceeding threshold.')
@click.option('--trend-start-year', type=int, default=None,
              help=('YYYY. The earliest year to consider when calculating a monthly trend image.'
                    ' Defaults to the first year data is available for the selected month.'))
# required options
@click.option('-h', '--hemi', type=click.Choice(['N', 'S', 'N,S', 'S,N']), default='N,S',
              help=('Hemisphere. If none is specified, create images for both hemispheres.'))
@click.option('-y', '--year', type=int, help=('YYYY. Year.'))
@click.option('-m', '--month', type=int, help=('MM. Month.'))
# required for --daily images
@click.option('-d', '--day', type=int, help=('DD. Day of the month.'))
# Required for --anomaly images
@click.option('--year-range', type=YearRange(),
              default='{},{}'.format(*nt.DEFAULT_CLIMATOLOGY_YEARS),
              help=('YYYY,YYYY. Years defining the climatology range. Defaults '
                    'to {},{}.'.format(*nt.DEFAULT_CLIMATOLOGY_YEARS)))
@seaicelogging.log_command(log)
def sii_image_geotiff(**kwargs):
    """sii_image_geotiff is a command line interface to create GeoTiff images of
    sea ice index extent and concentration data.


    \b
    Required Options:
        '--hemi', '--year', '--month'

    \b
    Feature Switches:
      Each of these pairs of options are mutually exclusive, and only one of
      the values should be supplied. If both are provied on the command line,
      the last one will take precedence.

    \b
      temporality:
        '--daily' [default], '--monthly'

    \b
      image_type:
        '--concentration' [default], '--extent', '--trend', '--anomaly'

    Usage examples:

    \b
    * Generate daily concentration geotiff.
       sii_image_geotiff --daily --concentration -h N -y 2012 -m 3 -d 14

    \b
    * Generate daily extent geotiff.
       sii_image_geotiff --daily --extent -h N -y 2012 -m 3 -d 14

    \b
    * Generate monthly extent geotiff.
       sii_image_geotiff --monthly --extent -h N -y 2012 -m 3
    """
    config = util.validate_command_line_options(kwargs)
    dates = util.get_dates(config)

    # Ensure the hemi entry is a list of hemispheres.
    config['hemi'] = list(config['hemi'].split(','))

    count = len(config['hemi']) * len(dates)
    log.info('Creating {count} image{s}...'.format(count=count,
                                                   s='' if count == 1 else 's'))

    # Iterate over all hemispheres and dates, creating an image for each pair.
    missing_dates = 0
    for hemi, date in product(config['hemi'], dates):
        try:
            api.geotiff_image(hemisphere=hemi,
                              date=date,
                              temporality=config['temporality'],
                              image_type=config['image_type'],
                              output=config['output'],
                              config_filename=config['config_filename'],
                              flatten=config['flatten'],
                              year_range=config['year_range'],
                              allow_bad_data=config['allow_bad_data'],
                              overwrite=config['overwrite'],
                              trend_start_year=config['trend_start_year'],
                              trend_clipping_threshold=kwargs['trend_clip'])
        except SeaIceImagesNoData:
            date_fmt = '%Y-%m-%d' if config['temporality'] == 'daily' else '%Y-%m'
            log.warning('Did not create GeoTiff for {} {}:'
                        ' no data.'.format(hemi, date.strftime(date_fmt)))
            missing_dates += 1

    # Alert the user appropriately if files were not created.
    num_created = count - missing_dates
    if num_created == 0:
        raise SeaIceImagesNoData('No data was found for the requested'
                                 ' dates. No GeoTiffs were created.')

    if num_created < count:
        missing_str = ' {} dates of data were '\
                      'missing.'.format(count - num_created)
    else:
        missing_str = ''

    log.info('{} GeoTiffs were created.{}'.format(num_created, missing_str))


if __name__ == '__main__':
    sii_image_geotiff()
