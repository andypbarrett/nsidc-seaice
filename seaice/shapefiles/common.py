import calendar as cal
import os
import tempfile
import zipfile
import logging

import fiona
from shapely import geometry

import seaice.nasateam as nt

log = logging.getLogger(__name__)

OCEAN = 0
ICE = 1
COAST = nt.FLAGS['coast']
LAND = nt.FLAGS['land']
MISSING = nt.FLAGS['missing']


def _clim_string(range):
    return '_{:04}-{:04}'.format(*range)


def _shapefile_name(config):
    """Returns a string containing the shapefile name (without file extension).

    Arguments
    ---------
    config: dictionary containing various settings.
        hemi: nt.NORTH or nt.SOUTH

        year: int

        month: int

        day: int

        dayofyear: int

        version_str: str

        polygon: True or False; incompatible with polyline

        polyline: True or False; incompatible with polygon

        median: True or False

        range: list of ints, defines the range of years for the median

    """
    if config['polygon']:
        kind = 'polygon'
    elif config['polyline']:
        kind = 'polyline'

    if config['median']:
        median_part = 'median_'
        clim_str = _clim_string(config['range'])
    else:
        median_part = ''
        clim_str = ''

    if 'dayofyear' in config:
        date_str = '{dayofyear:03}'.format(dayofyear=config['dayofyear'])

    elif 'year' in config and 'month' in config and 'day' not in config:
        date_str = '{year}{month:02}'.format(year=config['year'], month=config['month'])

    elif 'year' not in config and 'month' in config and 'day' in config:
        date_str = '{month:02}_{day:02}'.format(month=config['month'], day=config['day'])

    elif 'year' not in config and 'month' in config and 'day' not in config:
        date_str = '{month:02}'.format(month=config['month'])

    return '{median_part}extent_{hemi}_{date_str}{clim_str}_{kind}_{version}'.format(
        median_part=median_part,
        hemi=config['hemi']['short_name'],
        date_str=date_str,
        clim_str=clim_str,
        kind=kind,
        version=config['version_str']
    )


def _create_shapefile(config, *geoms):
    """Create a zip file containing a .shp and the other files composing a
    Shapefile. Returns the path to the zip file.

    Arguments
    ---------
    config: nasateam dictionary containing various settings.
        hemi: nt.NORTH or nt.SOUTH

        output_dir: directory in which to save the created .zip file

        polygon, polyline: determines what kind of shapefile to create; one of
            these options must be True, and the other False

    geoms: list of shapely.geometry.BaseGeometry objects that can be passed to
        shapely.geometry.mapping to write to a shapefile. If creating a polygon
        shapefile, these should be Polygon (or similar) objects; if creating a
        polyline shapefile, these should be MultiLineString objects.

    """
    shapefile_name = _shapefile_name(config)
    tree_struct = ''
    if not config['flatten']:
        tree_struct = _default_archive_paths(config)
    os.makedirs(os.path.join(config['output_dir'], tree_struct), exist_ok=True)

    shapefile_zip = os.path.join(config['output_dir'], tree_struct, shapefile_name + '.zip')

    if config['polygon']:
        schema = {'properties': {}, 'geometry': 'Polygon'}

    elif config['polyline']:
        schema = {'properties': {}, 'geometry': 'MultiLineString'}

    with tempfile.TemporaryDirectory() as tmpdir:
        shapefile_shp = os.path.join(tmpdir, shapefile_name + '.shp')

        with fiona.collection(shapefile_shp, 'w', 'ESRI Shapefile',
                              schema=schema, crs=config['hemi']['crs']) as output:
            for geom in geoms:
                output.write({'geometry': geometry.mapping(geom), 'properties': {}})

        with zipfile.ZipFile(shapefile_zip, 'w') as z:
            for f in os.listdir(tmpdir):
                z.write(os.path.join(tmpdir, f), arcname=f)
    log.info('Created {}'.format(shapefile_zip))
    return shapefile_zip


def _default_archive_paths(config):
    """
    Default output directory structure for writing shapefiles.  Output roots may be different.

     /hemi/monthly/shapefiles/shp_extent/[MM]_[Mon]/extent_[NS]_[YYYYMM]_poly[gon|line]_{ver}.zip
                             /shp_median/median_[NS]_[MM]_1981_2010_polyline_{ver}.zip
                             /dayofyear_median/median_extent_[NS}_[DOY]_1981-2010_polyline_{ver}.zip

    """

    log.debug('keys used to create archive paths')
    log.debug('month       %s', config.get('month', 'no key found for month'))
    log.debug('dayofyear   %s', config.get('dayofyear', 'no key found for dayofyear'))
    log.debug('median      %s', config.get('median', 'no key found for median'))
    log.debug('hemi        %s', config['hemi']['short_name'])

    if config.get('median', None):
        if config.get('dayofyear'):
            temporality = 'daily'
            last_dir = 'dayofyear_median'
        else:
            temporality = 'monthly'
            last_dir = 'shp_median'

        return os.path.join(config['hemi']['long_name'], temporality, 'shapefiles', last_dir)

    # It's not a median file, so we know how to build the output path.
    month_dir = '{:02}_{}'.format(config['month'], cal.month_abbr[config['month']])
    return os.path.join(config['hemi']['long_name'], 'monthly', 'shapefiles',
                        'shp_extent', month_dir)
