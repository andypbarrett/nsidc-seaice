import calendar as cal
import copy
import logging
import os
import re
import tempfile
import yaml
import zipfile

import fiona
import rasterio
import numpy as np
from shapely.geometry import MultiLineString

from .errors import SeaIceImagesBadConfiguration
from .errors import SeaIceImagesNotImplementedError
import seaice.nasateam as nt
import seaice.timeseries as sit


DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'ancillary', 'config.yml')

log = logging.getLogger(__name__)


def load_config(config_filename=None):
    """ Load a yaml configuration file from disk. """
    if config_filename is None:
        config_filename = DEFAULT_CONFIG_FILE

    with open(config_filename, 'r') as fp:
        cfg = yaml.load(fp)

    return cfg


def load_image_config(config_filename, hemi_name, date, temporality,
                      image_type='concentration', blue_marble=False, **kwargs):
    """Load config from file. Returns an interpolated and pruned appropriate
       configuration for generating a sea ice concentration images.

    Arguments:

    config_filename: configuration filename to load, if None, the default
                     configuration file will be used.

    hemi_name: one of either 'north' or 'south', generally provided as the
               nt.HEMI['long_name']

    date: a python datetime.date object

    temporality: flag with value in ['daily', 'monthy'].  Used to to select
                 correct configuation options that differ between monthly and
                 daily images.

    image_type: flag with value in ['concentration', 'extent', 'anomaly',
                                    'trend'].  Used to specify which type of
                                    sea ice image to create.

    kwargs: A dictionary that is merged into the configutation after
            promoting/pruning the north, south and concentration keys


    About the configuration file:

    Information that is specific to a given hemisphere is contained in the
    first level key 'north' or 'south', and the subkeys of these are promoted
    via merge into the parent's level of the config dictionary.

    e.g.: an input configuration yaml file with:
    -----
    south:
       image:
          pixel_dims: [316, 332]
          axes: southern axes
    north:
       image:
          pixel_dims: [304, 448]
          axes: northern axes
    image:
       background: 'background information'
    -----

    loaded with a hemisphere of 'north' would produce an object the same as if the input yaml was:
    -----
    image:
      pixel_dims: [304, 448]
      axes: northern axes
      background: 'background information'
    -----

    """
    log.debug('load_image_config(kwargs) => %s', kwargs)

    # manipulate config to get just what a make_image expects
    cfg = load_config(config_filename)
    cfg['config_filename'] = config_filename

    # promote either the north or south subkeys to the top level based on input argument.
    # cfg['north'][keyname] => cfg[keyname]
    cfg = _merge_keys(cfg, cfg[hemi_name])
    cfg = _prune_keys(cfg, 'north', 'south')

    # promote the current image_type's keys.
    cfg = _merge_keys(cfg, cfg[image_type])
    cfg = _prune_keys(cfg, image_type)

    # promote either the north or south subkeys from the image_type's keys to
    # the top level (note that at this point, image_type's keys have already
    # been promoted to the top)
    # cfg[image_type]['north'][keyname] => cfg[keyname]
    if hemi_name in cfg:
        cfg = _merge_keys(cfg, cfg[hemi_name])
        cfg = _prune_keys(cfg, 'north', 'south')

    # If a blue marble image is requested, merge those keys.
    cfg = _promote_blue_marble(cfg, image_type, blue_marble, hemi_name)

    # Update temporality keys
    if temporality in cfg.keys():
        cfg = _merge_keys(cfg, cfg[temporality])
        cfg = _prune_keys(cfg, temporality)

    if image_type == 'extent':
        # Remove the colorbar key. Not necessary for extent images.
        cfg = _prune_keys(cfg, 'colorbar')

    if cfg.get('median_extent_line'):
        # Get the median extent line
        cfg = _get_median_extent_line(cfg, hemi_name, date,
                                      temporality=temporality)

    # replace anything the user passed in as keyword arguments.
    cfg = _merge_keys(cfg, kwargs)

    # perform interpolation on colortable, and rescale if necessary.
    cfg = _substitute_colortable(cfg)

    # perform interpolation on all labels
    if date is not None:
        for label in cfg['image_labels']:
            cfg[label]['text'] = _format_label(cfg[label]['text'],
                                               cfg.get('values', {}),
                                               date,
                                               cfg[label].get('dateformat'))
    cfg = _update_scale_if_hires(cfg)
    cfg = _rescale_config(cfg)

    # Include the current hemisphere in the config
    cfg['hemisphere'] = {'north': 'N', 'south': 'S'}[hemi_name]

    return cfg


def load_special_config(config_filename, special_type, image_type='extent'):
    """Loads the google earth ("google"), science on a sphere ("sos"), or any other
    special type of image config.

    """
    cfg = load_config(config_filename)

    # Promote the image type's keys
    cfg = _merge_keys(cfg, cfg[image_type])
    cfg = _prune_keys(cfg, image_type)

    # Promote the special key
    cfg = _merge_keys(cfg, cfg[special_type])

    cfg = _substitute_colortable(cfg)

    return cfg


def _promote_blue_marble(cfg_in, image_type, blue_marble, hemi_name):
    cfg = copy.deepcopy(cfg_in)

    if blue_marble:
        # Promote the blue_marble key
        cfg = _merge_keys(cfg, cfg['blue_marble'])

        # Promote the blue marble's internal hemisphere key.
        # This promotes the blue-marble's hemisphere dependent
        # projection information
        cfg['blue_marble_image'] = _merge_keys(cfg['blue_marble_image'],
                                               cfg['blue_marble_image'][hemi_name])
        cfg['blue_marble_image'] = _prune_keys(cfg['blue_marble_image'], 'blue_marble_image')
        cfg['blue_marble_image'] = _prune_keys(cfg['blue_marble_image'], 'north', 'south')

        if hemi_name in cfg:
            # Merge the hemisphere again bc. the blue marble
            # config includes hemisphere specific config it
            # wants to overwrite.
            cfg = _merge_keys(cfg, cfg[hemi_name])
            cfg = _prune_keys(cfg, 'north', 'south')

        # promote the current image_type's blue-marble keys.
        if image_type in cfg:
            cfg = _merge_keys(cfg, cfg[image_type])
            cfg = _prune_keys(cfg, image_type)

        # Get the blue marble image
        cfg = _get_blue_marble_image(cfg)

    else:
        # Prune out the blue_marble tree
        cfg = _prune_keys(cfg, 'blue_marble')

    return cfg


def merge_titles(cfg_in):
    """Merges the title and sub-title by appending the
    sub-title's text to the title. The sub-title is removed.

    The blue marble images don't have a dedicated sub-title,
    but we do want to use the subtitle's text/formatting
    In the title.

    BM monthly images have a title comprised of the date
    + total extent/area. Pull the total extent/area
    subtitle text from the current image type's config
    to acheive this result. For example, the blue marble's
    title of 'November 2015' will have an extent image's
    subtitle text of 'Total extent = 16.6 million sq km'
    appended to it to obtain a complete title:
    'November 2015 Total extent = 16.6 million sq km'
    """
    cfg = copy.deepcopy(cfg_in)

    if 'sub-title' in cfg['image_labels']:
        cfg['image_labels'].remove('sub-title')
        sub_title = cfg.pop('sub-title')
        cfg['title']['text'] += ' {}'.format(sub_title['text'])

    return cfg


def figure_size_inches(cfg):
    """Returns a tuple of figuresize in inches provided pixel_dims & dots per inch are supplied."""
    return tuple(np.array(cfg['canvas']['pixel_dims']) / cfg['canvas']['dpi'])


def remove_legend(cfg_in):
    """Remove legend from image configuration"""
    cfg = copy.deepcopy(cfg_in)
    return _prune_keys(cfg, 'legend')


def update_if_missing_data(cfg_in, gridset):
    """Modify cfg to add a missing legend if the gridset's data has any missing values."""
    cfg = copy.deepcopy(cfg_in)

    if not _gridset_data_has_missing(gridset):
        cfg = _prune_keys(cfg, 'missing_legend')

    return cfg


def _gridset_data_has_missing(gridset):
    return np.any(gridset['data'] == gridset['metadata']['missing_value'])


def _substitute_colors(color_list, named_colors):
    """Given a list of colors or names, return a copy of the color_list where
    each instance of '{key}' is replaced by the value in named_colors['key']

    calling _substitute_colors with:
      color_list = ['{ocean}', '{land}', '#137AE3', '{missing}', '#1684EB']

      named_colors =  {'lake': '#133399', 'land': '#777777',
                       'missing': '#e9cb00', 'ocean': '#093c70'}

    would return ['#093c70', '#777777', '#137AE3', '#e9cb00', '#1684EB']

    This is a more general version of _substitute_colortable that can be used
    for to substitute colors more than just for the colortables.

    """

    colors = []

    for color in color_list:
        if isinstance(color, str):
            try:
                color_name = re.match('{(?P<color>.*)}', color).group('color')
            except AttributeError:
                color_name = None

            # if the named color is defined as a tuple, don't use str.format;
            # that would wrap the tuple in a string
            if isinstance(named_colors.get(color_name), tuple):
                color = named_colors[color_name]

            else:
                color = color.format(**named_colors)

        colors.append(color)

    return colors


def _substitute_colortable(cfg_in):

    """Replaces values in cfg_in['colortable'] that are specially formatted with
       '{name}' with the values from cfg_in['namedcolors']['name'].

    'cfg_in' is required to have keys 'colortable' and 'namedcolors', with list
    and dictionary values respectively.

    Raises a SeaIceImagesBadConfiguration if a 'colortable' value has no
    substitute in the 'namedcolors' dict.

    so an input config looking like:
    cfg_in = {'colortable': ['{ocean}', '{land}', '#137AE3', '{missing}', '#1684EB'],
              'namedcolors': {'lake': '#133399', 'land': '#777777',
                              'missing': '#e9cb00', 'ocean': '#093c70'}}

    will be transformed and have its values of {ocean}, {land}, and {missing}
    replaced and the output dictionary will look like:

    out = {'colortable': ['#093c70', '#777777', '#137AE3', '#e9cb00', '#1684EB'],
          'namedcolors': {'lake': '#133399', 'land': '#777777',
                          'missing': '#e9cb00', 'ocean': '#093c70'}}

    This is used to allow colortables some flexibility in selecting colors and
    to prevent colors that are used in the colortable as well as other places
    from being duplicated or more.

    """
    message = '''
    cfg_in['namedcolors'] must contain a complete substitution for every
    substitutable value in cfg['colortable'] for this function to succeed.
    '''

    cfg = copy.deepcopy(cfg_in)
    try:
        replaced = _substitute_colors(cfg['colortable'], cfg['namedcolors'])
    except KeyError as e:
        raise SeaIceImagesBadConfiguration(message) from e
    cfg['colortable'] = replaced
    return cfg


def set_source_attribute(cfg_in, seaicedatafilename):
    """ Set the source attribute based on the input sea ice filename. """
    cfg = copy.deepcopy(cfg_in)

    attribute = 'final data'
    try:
        if nt.DATA_FILENAME_MATCHER.search(seaicedatafilename).group('version') == 'nrt':
            attribute = 'near-real-time data'
        cfg['source_attribution'].update({'text': attribute})

    except AttributeError as e:
        log.error('seaicedatafilename "%s", wasn\'t a valid sea ice data filename '
                  'removing \'source_attribution\' from \'image_labels\'',
                  seaicedatafilename)
        try:
            cfg['image_labels'].remove('source_attribution')
        except ValueError as e:
            log.error('failed to remove \'source_attribution\' '
                      'from [\'image_labels\'] => %s', cfg['image_labels'])

    return cfg


def set_output(cfg_in, date, output, image_type, temporality, flatten,
               geotiff=False):
    cfg = copy.deepcopy(cfg_in)

    def default_filename():
        if temporality == 'daily':
            date_fmt = '%Y%m%d'
        elif temporality == 'monthly':
            if image_type == 'trend':
                date_fmt = '%m'
            else:
                date_fmt = '%Y%m'
        else:
            raise TypeError('{} is not a recognized temporality'.format(temporality))

        hemi_id = '{}_'.format(cfg.get('hemisphere')) if cfg.get('hemisphere', False) else ''
        hires_id = 'hires_' if cfg.get('hires', False) else ''
        google_id = 'google_' if cfg.get('google_image', False) else ''
        blue_marble_id = 'blmrbl_' if cfg.get('blue_marble_image', False) else ''
        file_extension = 'tif' if geotiff else 'png'

        return '{hemi}{date}_{type}_{blue_marble}{google}{hires}{version}.{ext}'.format(
            hemi=hemi_id,
            date=date.strftime(date_fmt),
            type=cfg['output_postfix'],
            hires=hires_id,
            google=google_id,
            blue_marble=blue_marble_id,
            version=cfg_in.get('output_version', nt.VERSION_STRING),
            ext=file_extension
        )

    # default (no --output)
    if output is None:
        root_dir = os.getcwd()
        tree_structure = _tree_structure(cfg.get('hemisphere'), temporality,
                                         date, flatten, geotiff)
        full_dir = os.path.realpath(os.path.join(root_dir, tree_structure))

        filename = default_filename()

    # --output is an existing directory
    elif os.path.isdir(output):
        root_dir = output
        tree_structure = _tree_structure(cfg.get('hemisphere'), temporality,
                                         date, flatten, geotiff)
        full_dir = os.path.realpath(os.path.join(root_dir, tree_structure))

        filename = default_filename()

    # --output must be a filename
    else:
        cfg['custom_filename'] = True
        full_dir = os.path.dirname(output)
        filename = os.path.basename(output)

    _ensure_path_exists(full_dir)

    cfg['output'] = os.path.realpath(os.path.join(full_dir, filename))

    return cfg


def set_sos_output(cfg_in, datetime_index, output, sensor):
    cfg = copy.deepcopy(cfg_in)

    start, end = datetime_index[0], datetime_index[-1]

    filename = 'nt_monthext_{start}-{end}_{sensor}_sos.png'.format(start=start.strftime('%Y%m%d'),
                                                                   end=end.strftime('%Y%m%d'),
                                                                   sensor=sensor)

    cfg['output'] = os.path.realpath(os.path.join(output, filename))

    return cfg


def _tree_structure(hemi, temporality, date, flatten, geotiff):
    if flatten:
        return os.path.curdir

    nt_hemi = nt.by_name(hemi)
    hemisphere = nt_hemi['long_name']

    year = {
        'daily': str(date.year),
        'monthly': ''
    }[temporality]

    month = '{:02}_{}'.format(date.month, cal.month_abbr[date.month])

    if geotiff:
        dir_type = 'geotiff'
    else:
        dir_type = 'images'

    tree = os.path.join(hemisphere,
                        temporality,
                        dir_type,
                        year,
                        month)

    return tree


def _ensure_path_exists(path):
    if os.path.isdir(path) or (path == ''):
        return

    os.makedirs(path, exist_ok=True)
    log.info('created {}/'.format(path))


def set_sub_title(cfg_in, date, image_type, temporality, gridset):
    """ find the sub-title.text value and replace any {area} with the string value in area.

    If area is blank '' or 'None', Don't add sub-title to the image_labels.
    """
    cfg = copy.deepcopy(cfg_in)

    if temporality != 'monthly' or image_type == 'trend':
        return cfg
    value = _monthly_data_millions_km2(cfg['hemisphere'], date, image_type, gridset)

    if value:
        new_text = cfg['sub-title']['text'].format(value=value)
        cfg['image_labels'].append('sub-title')
        cfg['sub-title'].update({'text': new_text})

    return cfg


def _format_label(label_txt, values, date, date_format=None):
    """
    Replaces '{date}' and other placeholders in label_txt by formatting with
    date string and values given by -v key=value
    """
    values = copy.deepcopy(values)

    if 'date' not in values:
        values['date'] = date.strftime(date_format or '')

    label_txt = label_txt.format(**values)
    return label_txt


def _rescale_fontsize(cfg_in, scale):
    """ Traverses cfg rescaling values of keys that contain the word 'fontsize'.

    This keeps fonts the correct size when a user has requested to scale the configuration.
    """
    cfg = copy.deepcopy(cfg_in)
    for key, value in cfg.items():
        if isinstance(value, dict):
            cfg[key] = _rescale_fontsize(value, scale)
        elif re.search('fontsize', key):
            cfg[key] = value * scale
    return cfg


def _rescale_config(cfg_in):
    """Read the cfg['canvas']['scale'] value and update all of the cfg values that
       depend on it.

    The default configuration yml is set to a scale of 1., if this value is
    different than one, scale the appropriate values in the configuration to
    match.
    So an input config dict like:
    {'canvas': {'pixel_dims': [100, 200], 'scale': 2.0},
     'title': {'kwargs': {'color': 'white', 'fontsize': 16.0},
               'position': [0.038, 0.953],
               'text': 'Sea Ice Concentration, 30 Jan 2015'}}

    would be transformed into:
    {'canvas': {'pixel_dims': array([ 200.,  400.]), 'scale': 2.0},
     'title': {'kwargs': {'color': 'white', 'fontsize': 32.0},
               'position': [0.038, 0.953],
               'text': 'Sea Ice Concentration, 30 Jan 2015'}}

    updating the pixel_dims, and fontsize while ignoring other values.

    """
    cfg = copy.deepcopy(cfg_in)
    scale = cfg['canvas'].get('scale', 1.)
    cfg['canvas']['pixel_dims'] = np.array(cfg['canvas']['pixel_dims']) * scale
    cfg = _rescale_fontsize(cfg, scale)
    return cfg


def _merge_keys(target_in, source):
    """ Take keys in the source dictionary and add or merge them into the target dictionary. """
    target = copy.deepcopy(target_in)

    for key, value in source.items():
        if key not in target_in:
            # If key doesn't exist in target dict. Add whatever value is on the source.
            target[key] = value
        elif isinstance(target_in[key], dict) and isinstance(value, dict):
            # If both target value and source value are dictionaries, update
            # target.
            target[key] = _merge_dicts(target[key], value)
        else:
            raise SeaIceImagesBadConfiguration(
                'promotion of "{key}" failed\n'
                'replacing existing keys not implemented'.format(key=key)
            )

    return target


def _prune_keys(in_dict, *keys):
    """remove key(s) and their values if they exist in the dict."""
    dict_ = copy.deepcopy(in_dict)

    for key in keys:
        if dict_.get(key):
            dict_.pop(key)
    return dict_


def _monthly_data_millions_km2(hemi, date, image_type, gridset):
    """ Returns the monthly data value for the hemi and date,
    and image type in millions of km2. For concentration images,
    this returns area in millions of km2. For extent images,
    this returns extent in millions of km2
    """
    if image_type == 'anomaly':
        return np.round(_total_concentration_value(gridset) / 1e6, 1)

    if image_type == 'concentration':
        data_column = 'total_area_km2'
    elif image_type == 'extent':
        data_column = 'total_extent_km2'
    else:
        raise SeaIceImagesNotImplementedError('The {} image_type does not map to '
                                              'a known column name'.format(image_type))
    try:
        data_frame = sit.monthly(hemi, date)
        data_mkm2 = data_frame.loc[date.strftime('%Y-%m')][data_column] / 1.e6
        round_data = np.around(data_mkm2, 1)
        if np.isnan(round_data):
            data_value = ''
        else:
            data_value = '{:.1f}'.format(round_data)
    except KeyError as e:
        data_value = ''

    return data_value


def _total_concentration_value(gridset):
    """Return the total concentration of the gridset in square kilometers.

    This function works for any gridset whose data values represent a percentage
    of concentration, positive or negative.

    """
    try:
        fractional_data = .01 * np.ma.masked_outside(gridset['data'],
                                                     *gridset['metadata']['valid_data_range'])
        nt_hemi = nt.by_name(gridset['metadata']['hemi'])
        value = np.sum(fractional_data * nt_hemi['grid_areas'])

    except KeyError as e:
        log.exception('No total concentration computed')
        value = 0.0

    return value


def _merge_dicts(a, b, path=None):
    'merges b into a, replacing a[key] with b[key] if '
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                _merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                # overwrite a's value with b
                log.debug('a[%s] %s => replaced with b[%s] %s', key, a[key], key, b[key])
                a[key] = b[key]
        else:
            log.debug('setting: a[%s] (%s) => %s', key, a.get(key, 'was unset'), b[key])
            a[key] = b[key]
    return a


def _update_scale_if_hires(cfg_in):
    """If hires config, update the scale by the value in the cfg['canvas']['hires_factor'] """
    cfg = copy.deepcopy(cfg_in)

    scale = cfg['canvas'].get('scale', 1.)
    if cfg.get('hires', False):
        scale *= cfg['canvas'].get('hires_factor', 2.)
        log.debug('updated scale to %s', scale)
    cfg['canvas']['scale'] = scale

    return cfg


def _get_median_extent_line(cfg_in, hemi_name, date, temporality='daily'):
    """Get the median extent lines from shapefiles."""
    cfg = copy.deepcopy(cfg_in)

    hemi = {'north': 'N', 'south': 'S'}[hemi_name]

    if temporality == 'daily':
        doy = str(date.timetuple().tm_yday).zfill(3)
        shp_name = 'median_extent_{hemi}_{doy}_1981-2010_polyline_{ver}'.format(
            hemi=hemi, doy=doy, ver=nt.VERSION_STRING
        )
        median_dir = 'dayofyear_median'

    else:
        shp_name = ('median_extent_{hemi}_{date}_'
                    '1981-2010_polyline_{ver}').format(hemi=hemi,
                                                       date=date.strftime('%m'),
                                                       ver=nt.VERSION_STRING)
        median_dir = 'shp_median'

    shp_path = os.path.join(nt.SEA_ICE_BASE_DIR,
                            'shapefiles',
                            hemi_name,
                            temporality,
                            'shapefiles',
                            median_dir,
                            '{}.zip'.format(shp_name))

    with zipfile.ZipFile(shp_path, 'r') as zf:
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extractall(tmpdir)
            shapefile = os.path.join(tmpdir, shp_name + '.shp')
            with fiona.open(shapefile, 'r') as collection:
                feature = collection.next()

    coords = feature['geometry']['coordinates']

    log.debug('median extent line geometry type is {}'.format(feature['geometry']['type']))
    if feature['geometry']['type'] == 'LineString':
        log.debug('converting median extent line geometry to MultiLineString')
        coords = [coords]

    cfg['median_extent_line'] = MultiLineString(coords)

    return cfg


def _get_blue_marble_image(cfg_in):
    cfg = copy.deepcopy(cfg_in)
    bm_dir = cfg['blue_marble_image']['bm_dir']
    img_filename = cfg['blue_marble_image']['bm_filename']
    filepath = os.path.join(bm_dir, img_filename)
    cfg['blue_marble_image']['image'] = rasterio.open(filepath).read()

    return cfg


def append_nrt_flag_to_output_filename(cfg_in, file_list):
    cfg = copy.deepcopy(cfg_in)
    if cfg['custom_filename']:
        return cfg

    ext = '_goddard'
    if [f for f in file_list if nt.DATA_FILENAME_MATCHER.search(f).group('version') == 'nrt']:
        ext = '_nrtsi'

    p = re.compile('(\.\w{3})')
    cfg['output'] = p.sub(r'{}\1'.format(ext), cfg['output'])
    return cfg
