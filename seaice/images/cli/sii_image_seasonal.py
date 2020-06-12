# Command line interface to generate seasonal sea ice images.
import copy
import datetime as dt
import os
from itertools import product

import click

from .. import config
from .. import image
from seaice import version_flag
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.data as sid

log = seaicelogging.init('seaice.images')


DEFAULT_SEASONAL_CONFIG_FILE = os.path.join(os.path.dirname(__file__),
                                            os.pardir, 'ancillary', 'config_seasonal.yml')


@click.command()
@version_flag
@click.option('-o', '--output', default=None,
              help='Output image filename or directory.')
@click.option('-c', '--config_filename', default=DEFAULT_SEASONAL_CONFIG_FILE,
              help='Alternative configuration yaml file.  Must have all necessary options.')
@click.option('--trend', 'image_type', flag_value='trend',
              help='(image_type) Create trend image.')
@click.option('--trend-clip', default=100, help='Clip all trends values exceeding threshold.')
@click.option('-y', '--year', type=int, default=dt.date.today().year,
              help=('YYYY. Year defining the end year for the trend range. Defaults '
                    'to {}.'.format(dt.date.today().year)))
@click.option('-h', '--hemi', type=click.Choice(['N', 'S', 'N,S', 'S,N']), default='N,S',
              help=('Hemisphere. If none is specified, create images for both hemispheres.'))
@click.option('-s', '--season', type=click.Choice(['spring', 'summer', 'autumn', 'winter', 'all']),
              default='all', help=('Season. If none is specified, create images for all seasons.'))
@click.option('-z', '--hires', is_flag=True, default=False,
              help='Create high resolution image. Will multiply scale by a constant '
              'and add \'_hires\' to the output filenames')
@seaicelogging.log_command(log)
# this function is based on the sii_image CLI and api.ice_image; because of the
# unique time period of a "season", a new function was necessary
def sii_image_seasonal(**kwargs):
    hemis = kwargs['hemi'].split(',')

    if kwargs['season'] == 'all':
        kwargs['season'] = ['spring', 'summer', 'autumn', 'winter']
    else:
        kwargs['season'] = [kwargs['season']]

    config_filename = kwargs.pop('config_filename')

    count = len(hemis) * len(kwargs['season'])
    log.info('Creating {count} image{s}...'.format(count=count,
                                                   s='' if count == 1 else 's'))

    # Iterate over all hemispheres and seasons, creating an image for each pair.
    for hemi, season in product(hemis, kwargs['season']):
        nt_hemi = nt.by_name(hemi)

        cfg = config.load_image_config(config_filename,
                                       nt_hemi['long_name'],
                                       date=None,
                                       temporality=None,
                                       **kwargs)

        cfg['image_type'] = kwargs['image_type']

        cfg['seasons'] = cfg.get('seasons', nt.SEASONS)
        nt.validate_seasons(cfg['seasons'])

        dates = nt.datetime_index_for_seasonal_trends(cfg['year'], tuple(cfg['seasons'][season]))
        cfg['year'] = dates[-1].year

        cfg = _set_output(cfg, hemi, season, kwargs['output'])

        # easiest to just set the source attribution; like the standard monthly
        # trend images, these use final *and* NRT data, so this text draws attention
        # to the NRT part
        cfg['source_attribution'].update({'text': 'near-real-time data'})

        # custom title, easier to set like this than wrangling the yaml config
        cfg['title']['text'] = 'Sea Ice Concentration Trends, {season} 1979-{year}'.format(
            season=season.capitalize(),
            year=cfg['year']
        )

        gridset = sid.concentration_seasonal_trend(
            hemisphere=nt_hemi,
            year=cfg['year'],
            season=season,
            search_paths=nt.DEFAULT_SEA_ICE_PATHS,
            seasons=cfg.get('seasons', nt.SEASONS),
            min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH,
            clipping_threshold=kwargs['trend_clip']
        )

        # generating the trend gridset with seaicedata takes a few minutes; this
        # commented section can be used during development in place of the above
        # call to `sid.concentration_seasonal_trend` to save time and make it
        # easier to iterate on image changes
        #
        # import pickle
        # pickle_filename = 'gridset_{}_{}.p'.format(season, hemi)
        # try:
        #     gridset = pickle.load(open(pickle_filename, 'rb'))
        #     print('loaded', pickle_filename)
        # except:
        #     print('generating gridset...')
        #     # load ice data grid
        #     gridset = sid.concentration_seasonal_trend(
        #         hemisphere=nt_hemi,
        #         year=cfg['year'],
        #         season=season,
        #         search_paths=nt.DEFAULT_SEA_ICE_PATHS,
        #         seasons=cfg.get('seasons', nt.SEASONS),
        #         min_days_for_valid_month=nt.MINIMUM_DAYS_FOR_VALID_MONTH
        #     )
        #     pickle.dump(gridset, open(pickle_filename, 'wb'))
        #     print('wrote', pickle_filename)

        image.make_image(gridset['data'], cfg)


def _set_output(cfg, hemi, season, output):
    cfg = copy.deepcopy(cfg)

    default_filename = '{hemi}_{type}_{season}_1979-{year}_{hires}{version}.png'.format(
        hemi=hemi,
        type=cfg['image_type'],
        season=season,
        year=cfg['year'],
        hires='hires_' if cfg.get('hires', False) else '',
        version=nt.VERSION_STRING
    )

    # default (no --output)
    if output is None:
        root_dir = os.getcwd()
        full_dir = os.path.realpath(os.path.join(root_dir))

        filename = default_filename

    # --output is an existing directory
    elif os.path.isdir(output):
        root_dir = output
        full_dir = os.path.realpath(os.path.join(root_dir))

        filename = default_filename

    # --output must be a filename
    else:
        cfg['custom_filename'] = True
        full_dir = os.path.dirname(output)
        filename = os.path.basename(output)

    config._ensure_path_exists(full_dir)

    cfg['output'] = os.path.realpath(os.path.join(full_dir, filename))

    return cfg


if __name__ == '__main__':
    sii_image_seasonal()
