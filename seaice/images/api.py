import copy
import functools
import logging
import os

import numpy as np
from scipy.ndimage.interpolation import zoom

from . import config
from . import geotiff
from . import image
from .errors import SeaIceImagesNoData
from seaice.logging import log_duration
import seaice.nasateam as nt
import seaice.data as sid

log = logging.getLogger(__name__)

# Factor used to upsample the input concentrations, the larger this is, the
# smoother the extent images, but also the longer it takes to make one.
BLUE_MARBLE_SCALE_FACTOR = 2
GOOGLE_SCALE_FACTOR = 4
SOS_SCALE_FACTOR = 4


def ice_image(hemisphere, date,
              temporality='daily',
              image_type='concentration',
              output=None,
              config_filename=None,
              flatten=False,
              allow_bad_data=False,
              blue_marble=False,
              overwrite=True,
              trend_clipping_threshold=100,
              **kwargs):
    """Create an image for the sea ice index. Returns a dict containing metadata
    about the created image.

    Arguments:

    hemisphere:  hemisphere identifier string. "N" or "S"

    date: python datetime date object, for monthly temporality, any day value is fine.

    Keyword Arguments:

    temporality: flag with value 'daily' or 'monthly'.  This flag determines
    which type of concentration image is being generated.  It is used to pick
    information from the configuation file to determine how to format the date,
    whether or not to add a sub-title and how to name default outputfile.

    image_type: flag with value 'concentration' or 'extent'.  This flag
    determines which type of image to create.

    output: Image output path. Can be a filename, filename with full path, or
            path to an existing directory.

    config_filename: optional non-default configuration file.

    allow_bad_data: Flag to control whether bad data should create a special
                    "NO DATA" image or just display whatever data was pulled
                    from seaice.data.  The default is 'False', meaning a NO DATA
                    image is generated, set to truthy if you want to visualize
                    the data.

    blue_marble: Boolean flag that creates a version of the requested image type
        with the blue marble background if True. Only compatible with 'extent' and
        'concentration' image types.

    kwargs: Any further values to override in the loading of the config.  for
            example to make a double sized image you would pass in
            `canvas={'scale': 2}`, this is passed to load_image_config,
            Or of course you can just pass in a dict with **dict.

    """
    log.debug('ice_image(kwargs) => %s', kwargs)

    # load hemisphere
    nt_hemi = nt.by_name(hemisphere)

    # Load basic config
    cfg = config.load_image_config(config_filename,
                                   nt_hemi['long_name'], date,
                                   temporality, image_type=image_type,
                                   blue_marble=blue_marble,
                                   **kwargs)
    cfg = config.set_output(cfg,
                            date,
                            output,
                            image_type,
                            temporality,
                            flatten)

    if (not overwrite) and os.path.isfile(cfg['output']):
        log.info('file already exists; skipping {}'.format(cfg['output']))
        return

    is_no_data_image = False

    # load ice data grid
    try:
        gridset, cfg = _get_ice_data(nt_hemi, date, temporality, allow_bad_data, cfg,
                                     data_type=image_type, year_range=cfg['year_range'],
                                     blue_marble=blue_marble,
                                     trend_start_year=cfg.get('trend_start_year', None),
                                     trend_clipping_threshold=trend_clipping_threshold)
    except SeaIceImagesNoData:
        gridset = _nodata_background_gridset(nt_hemi, date, blue_marble)
        cfg['image_labels'].append('no_data')
        gridset['metadata']['no_data'] = True
        is_no_data_image = True

        if(image_type == 'anomaly'):
            cfg = config.remove_legend(cfg)

    cfg = config.set_sub_title(cfg, date, image_type, temporality, gridset)

    if blue_marble:
        # merge the title and subtitle
        cfg = config.merge_titles(cfg)

    cfg = config.update_if_missing_data(cfg, gridset)
    cfg = config.set_source_attribute(cfg, _source_filename(gridset['metadata']))
    image.make_image(gridset['data'], cfg)

    return {
        'arguments': dict(hemisphere=hemisphere,
                          date=date,
                          temporality=temporality,
                          image_type=image_type,
                          output=output,
                          config_filename=config_filename,
                          flatten=flatten,
                          allow_bad_data=allow_bad_data,
                          blue_marble=blue_marble,
                          overwrite=overwrite,
                          **kwargs),
        'filepath': cfg['output'],
        'is_no_data_image': is_no_data_image
    }


def google_earth_image(date,
                       temporality='monthly',
                       image_type='extent',
                       output=None,
                       config_filename=None,
                       allow_bad_data=False,
                       overwrite=True,
                       trend_clipping_threshold=100):
    cfg = config.load_special_config(config_filename, 'google', image_type=image_type)
    cfg = config.set_output(cfg,
                            date,
                            output,
                            image_type,
                            temporality,
                            flatten=True)

    if (not overwrite) and os.path.isfile(cfg['output']):
        log.info('file already exists; skipping {}'.format(cfg['output']))
        return

    try:
        north_gridset, cfg = _get_ice_data(nt.NORTH, date, temporality,
                                           allow_bad_data, cfg, data_type=image_type, google=True,
                                           trend_clipping_threshold=trend_clipping_threshold)

        south_gridset, cfg = _get_ice_data(nt.SOUTH, date, temporality,
                                           allow_bad_data, cfg, data_type=image_type, google=True,
                                           trend_clipping_threshold=trend_clipping_threshold)

    except SeaIceImagesNoData as e:
        log.info('SeaIceImageNoData raised and captured for _get_ice_data: {}-{}.  Skipping'.format(
            date.year, date.month))
        return

    # Add custom extension if no custom filename is specified
    file_list = north_gridset['metadata']['files'] + south_gridset['metadata']['files']
    cfg = config.append_nrt_flag_to_output_filename(cfg, file_list)

    north_gridset, cfg['north'] = _prepare_ice_no_land(north_gridset,
                                                       image_type,
                                                       cfg['north'],
                                                       scale_factor=GOOGLE_SCALE_FACTOR,
                                                       order=1)

    south_gridset, cfg['south'] = _prepare_ice_no_land(south_gridset,
                                                       image_type,
                                                       cfg['south'],
                                                       scale_factor=GOOGLE_SCALE_FACTOR,
                                                       order=1)

    image.make_plate_carree_image(cfg, image_type, north_gridset, south_gridset)

    return {
        'arguments': dict(date=date,
                          temporality=temporality,
                          image_type=image_type,
                          output=output,
                          config_filename=config_filename,
                          allow_bad_data=allow_bad_data,
                          overwrite=overwrite),
        'filepath': cfg['output']
    }


def sos_image(date_range, output, config_filename, allow_bad_data, overwrite):
    cfg = config.load_special_config(config_filename, 'sos')

    image_type = 'extent'

    try:
        north_gridset = _get_ice_data_sos('N', date_range, allow_bad_data)
        south_gridset = _get_ice_data_sos('S', date_range, allow_bad_data)
    except SeaIceImagesNoData as e:
        log.info('SeaIceImageNoData raised and captured for _get_ice_data: {}.  Skipping'.format(
            date_range))
        return

    sensor_string = _sensor_string(north_gridset, south_gridset)
    cfg = config.set_sos_output(cfg, date_range, output, sensor_string)

    if (not overwrite) and os.path.isfile(cfg['output']):
        log.info('file already exists; skipping {}'.format(cfg['output']))
        return

    north_gridset, cfg['north'] = _prepare_ice_no_land(north_gridset,
                                                       image_type,
                                                       cfg['north'],
                                                       scale_factor=SOS_SCALE_FACTOR,
                                                       order=1)

    south_gridset, cfg['south'] = _prepare_ice_no_land(south_gridset,
                                                       image_type,
                                                       cfg['south'],
                                                       scale_factor=SOS_SCALE_FACTOR,
                                                       order=1)

    image.make_plate_carree_image(cfg, image_type, north_gridset, south_gridset)

    return {
        'arguments': dict(date_range=date_range,
                          output=output,
                          config_filename=config_filename,
                          allow_bad_data=allow_bad_data,
                          overwrite=overwrite),
        'filepath': cfg['output']
    }


def geotiff_image(hemisphere, date,
                  temporality='daily',
                  image_type='concentration',
                  output=None,
                  config_filename=None,
                  flatten=False,
                  allow_bad_data=False,
                  overwrite=True,
                  trend_clipping_threshold=100,
                  **kwargs):
    """Create a geotiff image for the sea ice index. Returns a dict containing
    metadata about the created image.

    Arguments:

    hemisphere:  hemisphere identifier string. "N" or "S"

    date: python datetime date object, for monthly temporality, any day value is fine.

    Keyword Arguments:

    temporality: flag with value 'daily' or 'monthly'.  This flag determines
                 which type of image is being generated.

    image_type: flag with value 'concentration', 'extent', 'anomaly', or
                'trend'.  This flag determines which type of image to create.

    output: Image output path. Can be a filename, filename with full path, or
            path to an existing directory.

    flatten: Flag to control whether output geotiffs are created without the
             default archive directory structure.

    config_filename: optional non-default configuration file.

    allow_bad_data: Flag to control whether bad data is allowed. The default is
                    'False'.

    kwargs: Any further values to override in the loading of the config.  for
            example to make a double sized image you would pass in
            `canvas={'scale': 2}`, this is passed to load_image_config,
            Or of course you can just pass in a dict with **dict.

    """

    # load hemisphere
    nt_hemi = nt.by_name(hemisphere)

    # Load basic config
    cfg = config.load_image_config(config_filename,
                                   nt_hemi['long_name'], date,
                                   temporality, image_type=image_type,
                                   **kwargs)

    # Set the ouput filepath and use the full image_type name in the filename.
    cfg['output_postfix'] = image_type
    cfg = config.set_output(cfg, date, output, image_type, temporality, flatten,
                            geotiff=True)

    if (not overwrite) and os.path.isfile(cfg['output']):
        log.info('file already exists; skipping {}'.format(cfg['output']))
        return

    # load ice data grid
    gridset, cfg = _get_ice_data(nt_hemi, date, temporality, allow_bad_data,
                                 cfg, data_type=image_type, year_range=cfg['year_range'],
                                 trend_start_year=cfg.get('trend_start_year', None),
                                 trend_clipping_threshold=trend_clipping_threshold)

    # Adjust the datatypes and values of extent/conc data for creating the
    # geotiffs.
    if image_type == 'extent':
        gridset['data'] = gridset['data'].astype(np.uint8)
    elif image_type == 'concentration':
        # Scale the data by 10 so that a colormap can be created. Float values
        # cannot be used to lookup colormap entries.
        gridset['data'] = gridset['data'] * 10
        gridset['data'] = gridset['data'].astype(np.uint16)

        # Similarily scale the colorbounds so the associated colortable
        # references the correct values.
        cfg['colorbounds'] = [c * 10 for c in cfg['colorbounds']]
    elif image_type == 'anomaly':
        gridset['data'] = gridset['data'].astype(np.float)
        cfg['colortable'] = None
    elif image_type == 'trend':
        cfg['colortable'] = None

    # Make the geotiff.
    geotiff.make_geotiff(cfg, nt_hemi, gridset)

    return {
        'arguments': dict(hemisphere=hemisphere,
                          date=date,
                          temporality=temporality,
                          image_type=image_type,
                          output=output,
                          config_filename=config_filename,
                          flatten=flatten,
                          allow_bad_data=allow_bad_data,
                          overwrite=overwrite,
                          **kwargs),
        'filepath': cfg['output']
    }


def _sensor_string(*gridsets):
    sensors = []

    for gridset in gridsets:
        matches = [nt.DATA_FILENAME_MATCHER.match(f) for f in gridset['metadata']['files']]
        sensors += [match.group('platform') for match in matches if match is not None]

    # get the unique sensors in chronological order
    unique_sensors = []
    for sensor in sensors:
        if sensor not in unique_sensors:
            unique_sensors.append(sensor)

    sensor_string = '-'.join(unique_sensors)
    log.debug('derived this sensor_string taken from the gridsets: {}'.format(sensor_string))

    return sensor_string


def _source_filename(metadata):
    """ Return the first metadata file in a list, and an empty string if the list is empty."""
    data_type = metadata.get('type', None)
    if data_type == 'Monthly Anomaly':
        key = 'month_files'
    elif data_type == 'Monthly Trend':
        key = 'filename'
    else:
        key = 'files'

    files = metadata.get(key, [])
    if len(files) == 0:
        return ''
    return files[0]


def _nodata_background_gridset(nt_hemi, date, blue_marble):
    gridset = _land_coast_gridset(nt_hemi, date)
    if blue_marble:
        gridset['data'] = np.ma.masked_all_like(gridset['data'])

    return gridset


def _land_coast_grid(nt_hemi, month_number):
    # make a ocean/land/coast mask.
    loci = nt.loci_mask(nt_hemi, month_number)
    grid = (loci.data * nt_hemi['mask']['ocean']).astype(np.float)
    grid[loci == nt_hemi['mask']['land']] = nt.FLAGS['land']
    grid[loci == nt_hemi['mask']['coast']] = nt.FLAGS['coast']

    return grid


def _land_coast_gridset(nt_hemi, date):
    """Take the existing configuration, and make a no_data image.

    Create a gridset with data that is just ocean, land, and coast with the
    values from nasateam.

    """
    gridset = {}
    gridset['metadata'] = {'files': [''],
                           'missing_value': 255.}
    gridset['data'] = _land_coast_grid(nt_hemi, date.month)

    return gridset


def _get_ice_data(nt_hemi, date, temporality, allow_bad_data, cfg_in, data_type='concentration',
                  year_range=None, blue_marble=False, google=False, trend_start_year=None,
                  trend_clipping_threshold=None):
    """Get the seaicedata.gridset for the desired hemisphere, date, data type and temporality"""
    log.debug('_get_ice_data(data_type(%s), temporality(%s), blue_marble(%s)):',
              data_type, temporality, blue_marble)

    cfg = copy.deepcopy(cfg_in)

    if blue_marble or google:  # for smooth extent images, start with original concentration
        image_type = data_type
        data_type = 'concentration'
    try:
        if (data_type, temporality) == ('concentration', 'daily'):
            gridset = sid.concentration_daily(nt_hemi,
                                              date.year,
                                              date.month,
                                              date.day,
                                              drop_invalid_ice=True,
                                              allow_bad_dates=allow_bad_data,
                                              allow_empty_gridset=allow_bad_data)

        elif (data_type, temporality) == ('concentration', 'monthly'):
            gridset = sid.concentration_monthly(nt_hemi,
                                                date.year,
                                                date.month,
                                                drop_invalid_ice=True,
                                                allow_empty_gridset=allow_bad_data)

        elif (data_type, temporality) == ('extent', 'daily'):
            gridset = sid.extent_daily(nt_hemi,
                                       year=date.year,
                                       month=date.month,
                                       day=date.day,
                                       allow_empty_gridset=allow_bad_data)

        elif (data_type, temporality) == ('extent', 'monthly'):
            gridset = sid.extent_monthly(nt_hemi,
                                         year=date.year,
                                         month=date.month,
                                         allow_empty_gridset=allow_bad_data)

        elif (data_type, temporality) == ('anomaly', 'monthly'):
            gridset = sid.concentration_monthly_anomaly(hemisphere=nt_hemi,
                                                        year=date.year,
                                                        month=date.month,
                                                        start_year=year_range[0],
                                                        end_year=year_range[1],
                                                        allow_empty_gridset=allow_bad_data)

        elif (data_type, temporality) == ('trend', 'monthly'):
            gridset = sid.concentration_monthly_trend(hemisphere=nt_hemi,
                                                      year=date.year,
                                                      month=date.month,
                                                      trend_start_year=trend_start_year,
                                                      clipping_threshold=trend_clipping_threshold)

        else:
            raise NotImplementedError('{} {} images cannot be generated.'.format(temporality,
                                                                                 data_type))

        if blue_marble:
            gridset, cfg = _prepare_ice_no_land(gridset, image_type, cfg, BLUE_MARBLE_SCALE_FACTOR)

    except sid.errors.SeaIceDataNoData as e:
        log.warning('_get_ice_data found no data for %s, %s, %s',
                    nt_hemi['short_name'], date.strftime('%Y-%m-%d'), temporality)
        raise SeaIceImagesNoData(e)

    return gridset, cfg


def _get_ice_data_sos(hemi, date_range, allow_bad_data):
    try:
        gridset = sid.concentration_daily_average_over_date_range(
            hemi,
            date_range,
            search_paths=nt.DEFAULT_SEA_ICE_PATHS,
            allow_empty_gridset=allow_bad_data,
            drop_land=True,
            drop_invalid_ice=True
        )
    except sid.errors.SeaIceDataNoData as e:
        log.warning('_get_ice_data_sos found no data for %s, %s', hemi, str(date_range))
        raise SeaIceImagesNoData(e)

    return gridset


def _prepare_concentration_no_land(gridset):
    """Blue marble images display ice atop the NASA blue marble image.  So we need
     to remove land for all images and remove ice < 15% for concentration images.
    """
    filters = []
    filters.append(functools.partial(sid.filters.drop_land, nt.FLAGS['land'],
                                     nt.FLAGS['coast']))

    filters.append(functools.partial(sid.filters.concentration_cutoff,
                                     nt.EXTENT_THRESHOLD))

    gridset = sid.filters.apply_filters(gridset, filters)

    gridset['data'] = np.ma.masked_where(gridset['data'] < 1, gridset['data'])
    return gridset


@log_duration(log, 'DEBUG')
def _prepare_extent_no_land(in_gridset, scale_factor, order=1):
    """Take a concentration gridset and upsample so that we have blue marble extents"""
    gridset = copy.deepcopy(in_gridset)

    gridset = sid.filters.drop_land(nt.FLAGS['land'], nt.FLAGS['coast'], gridset)

    # We have to set the pole to 100% ice and any missing to 0% ice.
    gridset['data'][gridset['data'] == nt.FLAGS['pole']] = 100
    gridset['data'][gridset['data'] == nt.FLAGS['missing']] = 0

    zoomed = zoom(gridset['data'], scale_factor, order=order)
    zoomed = _merge_missing(zoomed, in_gridset['data'], scale_factor)

    gridset['data'] = zoomed
    gridset = sid.filters.concentration_cutoff(nt.EXTENT_THRESHOLD, gridset)

    gridset['data'] = np.ma.masked_where(gridset['data'] < 1, gridset['data'])
    return gridset


def _prepare_ice_no_land(gridset, image_type, cfg_in, scale_factor, order=1):
    cfg = copy.deepcopy(cfg_in)
    if image_type == 'extent':
        for key in ('pixel_width', 'pixel_height'):
            cfg['projection'][key] = cfg['projection'][key] / scale_factor
        return _prepare_extent_no_land(gridset, scale_factor=scale_factor, order=order), cfg
    elif image_type == 'concentration':
        return _prepare_concentration_no_land(gridset), cfg


def _merge_missing(zoomed, original, scale_factor):
    """If any missing in original grid, zoom it (via nearest neighbor) and overlay onto the zoomed grid.

    We do this so that you don't smear any missing data gridcells, they will
    remain jagged, while the extents are smoothed.

    """
    only_missing = (original == nt.FLAGS['missing']).astype(np.int) * nt.FLAGS['missing']
    only_missing = zoom(only_missing, scale_factor, order=0)
    zoomed[only_missing != 0] = nt.FLAGS['missing']

    return zoomed
