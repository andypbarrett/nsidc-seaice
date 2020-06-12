# makes sea ice images.
from functools import lru_cache
from subprocess import run
import logging
import os
import time

import cartopy
import cartopy.crs as ccrs
import fiona
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.switch_backend('AGG')  # noqa
import matplotlib.patheffects as path_effects
import matplotlib.patches as patches
import numpy as np
from scipy.ndimage.interpolation import zoom
from shapely.geometry import MultiLineString

from . import config
from . import util
from seaice.logging import log_duration


log = logging.getLogger(__name__)


def _add_locations(ax, locations, loc_kwargs, loc_path_effects):
    loc_kwargs = loc_kwargs or {}

    for loc in locations:
        txt = ax.text(*loc['coords'], loc['name'], transform=ccrs.Geodetic(),
                      rotation=loc.get('rotation', 'horizontal'),
                      color=loc.get('color', 'white'),
                      **loc_kwargs)

        if loc['name'] in [path_loc['name'] for path_loc in loc_path_effects]:
            p = [lp for lp in loc_path_effects if lp['name'] == loc['name']][0]
            txt.set_path_effects([path_effects.Stroke(linewidth=3, foreground=p['foreground']),
                                  path_effects.Normal()])


def _add_colorbar(fig, cmap, norm, cfg):

    try:
        cb_cfg = cfg['colorbar']
    except KeyError:
        log.debug('Did not find a colorbar entry in cfg.')
        return

    ax = fig.add_axes(cb_cfg['axes'])

    bounds = cfg['colorbounds'][slice(*cb_cfg['bounds'])]
    ticks = cb_cfg['ticks']
    orientation = cb_cfg.get('orientation', 'vertical')
    cb2 = mpl.colorbar.ColorbarBase(ax, norm=norm,
                                    cmap=cmap,
                                    boundaries=bounds,
                                    extend=cb_cfg.get('extend', 'neither'),
                                    ticks=ticks,
                                    orientation=orientation,
                                    spacing='proportional')

    ticklabels = [str(round(b)) + '%' for b in ticks]
    cb2.set_ticklabels(ticklabels)

    # Modify the ticklabels along the colorbar's
    # axis.
    get_ticklabels = {'vertical': cb2.ax.get_yticklabels,
                      'horizontal': cb2.ax.get_xticklabels}[orientation]
    for tick in get_ticklabels():
        tick.set_color(cb_cfg['tick_color'])
        tick.set_fontsize(cb_cfg['tick_fontsize'])

    try:
        cb2.set_label(cb_cfg['label']['text'], **cb_cfg['label']['kwargs'])
    except KeyError as e:
        pass


def _add_text(ax, cfg, key):
    try:
        dict_ = cfg[key]
        ax.text(*dict_['position'], dict_['text'], **dict_['kwargs'])

    except KeyError:
        log.debug('Did not/Could not add text for: cfg[{}], {}.'.format(
            key, cfg.get(key, 'No key found in config')))


def _add_legend(ax, cfg, legend_key):

    try:
        leg_cfg = cfg[legend_key]
    except KeyError:
        log.debug('Did not find {} legend entry in cfg.'.format(legend_key))
        return

    edgecolor = leg_cfg.get('edgecolor', 'none')
    facecolor = cfg['namedcolors'].get(leg_cfg['namedcolor_name'])

    rect_shape = mpl.patches.Patch(edgecolor=edgecolor, facecolor=facecolor)
    leg = ax.legend([rect_shape],
                    [leg_cfg['text']],
                    prop={'size': leg_cfg['fontsize']},
                    handlelength=leg_cfg['handlesize'],
                    handleheight=leg_cfg['handlesize'],
                    loc=leg_cfg['loc'])

    # Set the legend text color
    for text in leg.get_texts():
        text.set_color(leg_cfg['text_color'])

    leg.get_frame().set_alpha(leg_cfg.get('alpha', 0))
    leg.get_frame().set_color(leg_cfg.get('legend_bg_color', 'none'))

    # Optionally set the legend to be placed relative to the figure,
    # rather than the map's axes.
    try:
        leg.set_bbox_to_anchor(leg_cfg['bbox_to_anchor'],
                               transform=plt.gcf().transFigure)
    except KeyError:
        log.debug('{} positioned relative to the map\'s geo-axes'.format(legend_key))

    ax.add_artist(leg)


def _add_median_extent_line(ax, proj, cfg):
    """Adds a median ice extent line"""
    try:
        geom = cfg['median_extent_line']
    except KeyError:
        log.debug('No median_extent_line found in cfg.')
        return

    feature = cartopy.feature.ShapelyFeature(geom, proj)

    line_color = cfg['namedcolors'].get('extent_line')

    scale = cfg['canvas'].get('scale', 1)
    contour_width = cfg['canvas'].get('contour_width', 1)
    linewidth = contour_width * scale

    ax.add_feature(feature, facecolor='none',
                   edgecolor=line_color, linewidth=linewidth)


def _add_polyline_overlays(ax, cfg):
    for overlay in cfg.get('polyline_overlays', []):
        geom = _get_polyline_geom(overlay['path'], overlay['id'], cfg['config_filename'])

        ax.add_feature(cartopy.feature.ShapelyFeature(geom, getattr(ccrs, overlay['ccrs'])()),
                       facecolor='none',
                       edgecolor=overlay['color'],
                       linewidth=overlay['width'] * cfg['canvas'].get('scale', 1))


@lru_cache(maxsize=8)
def _get_polyline_geom(path, line_id, config_filename):
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(config_filename), path)

    collection = fiona.open(path, 'r')

    coords = []
    for shape in collection:
        for coord in shape['geometry']['coordinates']:
            coords.append(coord)

    return MultiLineString(coords)


def _add_bm_image(cfg, image_axes, proj):
    """Display a projected blue marble image in the geo-axes."""
    try:
        bm_data = cfg['blue_marble_image']['image']
    except KeyError:
        log.debug('No blue marble image found in cfg.')
        return

    bm_data, projected_bounds = util.reproject_bm_image(bm_data, cfg, proj)
    bm_data = util.mask_bm_image(bm_data)
    bm_data = zoom(bm_data, (.25, .25, 1), order=0)

    # apply a gamma transformation to all but the alpha channel.
    bm_data[:, :, :-1] = util.apply_gamma(np.nan_to_num(bm_data[:, :, :-1]),
                                          data_min=0, data_max=255,
                                          gamma=cfg['gamma'])

    # Divide by 255 because bm_data.dtype == float. Matplotlib
    # expects float rgb images to be scaled between 0-1.
    bm_data[:, :, :-1] = bm_data[:, :, :-1] / 255.0

    start = time.time()

    image_axes.imshow(bm_data,
                      transform=proj,
                      origin='upper',
                      extent=projected_bounds,
                      interpolation='none')

    log.debug('Finished imshow of blue marble in '
              '{} seconds for {}'.format(time.time() - start, cfg['output']))

    # Hide the boundary of the projected space.
    image_axes.outline_patch.set_visible(False)

    # Make the the geo-axes transparent. We do this
    # because transparent pixels at the edge of the
    # blue marble will otherwise appear white (
    # the default color).
    image_axes.background_patch.set_visible(False)

    # Make sure the whole globe is shown
    image_axes.set_global()


def _create_figure(cfg, proj):
    """Given cfg and a cartopy proj object, return
    figure and axes objects.
    """
    # Create the figure
    fig = plt.figure(
        figsize=(config.figure_size_inches(cfg)),
        dpi=cfg['canvas']['dpi'],
        edgecolor='none'
    )
    fig.patch.set_facecolor(cfg['namedcolors']['background'])

    image_axes = fig.add_axes(cfg['image']['axes'], projection=proj)

    return fig, image_axes


def _save_figure(cfg, fig):
    if 'alpha' in cfg.keys():
        fig.patch.set_alpha(cfg.get('alpha'))
    fig.savefig(cfg['output'], dpi=cfg['canvas']['dpi'],
                facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)


def _run_imagemagick_convert(cfg):
    filename = cfg['output']
    args_list = cfg['image'].get('imagemagick_convert_args', [])

    for args in args_list:
        run('convert {args}'.format(args=args).format(filename=filename), shell=True)


@log_duration(log, 'DEBUG')
def _show_ice_grid(image_axes, ice_grid, proj, extent, ct_cmap, ct_norm, interpolation='nearest'):
    image_axes.imshow(ice_grid,
                      transform=proj,
                      origin='upper',
                      extent=extent,
                      interpolation=interpolation,
                      cmap=ct_cmap, norm=ct_norm)


def _add_gridlines(image_axes, cfg):
    if cfg.get('blue_marble_image'):
        gl = image_axes.gridlines(color='gray', linestyle='-')
        gl.ylocator = mpl.ticker.FixedLocator([89.5, 60,  30, 0, -30, -60, -89.5])
        gl.xlocator = mpl.ticker.FixedLocator(np.arange(13) * 30)
    else:
        gl = image_axes.gridlines()

    # n_steps is the number of interpolation points used to draw gridlines.
    # The default (30) is too low and causes lines of latitude to be jagged.
    gl.n_steps = 80


def _add_labels(image_axes, fig, cfg):
    for label_name in cfg['image_labels']:
        _add_text(fig, cfg, label_name)


def _get_map_projections(cfg):
    """Returns a proj, data_proj tuple. Proj is the map's projection,
    data_proj is the projection of ice grid and extent line data
    """
    if cfg.get('blue_marble_image'):
        proj = util.BlueMarbleProj(**cfg['blue_marble_image']['projection']['ccrs'])
        data_proj = ccrs.Stereographic(**cfg['projection']['ccrs'])
    else:
        proj = ccrs.Stereographic(**cfg['projection']['ccrs'])
        data_proj = proj

    return proj, data_proj


@log_duration(log, 'DEBUG')
def make_image(ice_grid, cfg):
    proj, data_proj = _get_map_projections(cfg)

    fig, image_axes = _create_figure(cfg, proj)

    # Add the blue marble image.
    _add_bm_image(cfg, image_axes, proj)

    ct_cmap, ct_norm = mpl.colors.from_levels_and_colors(
        cfg['colorbounds'], cfg['colortable']
    )
    extent = cfg['projection']['bounds']

    # Pre-project the ice grid
    src_pixel_height = cfg['projection']['pixel_height']
    src_pixel_width = cfg['projection']['pixel_width']
    ice_grid, new_extent = util.reproj_ice_grid(ice_grid, data_proj, extent, proj,
                                                src_pixel_width=src_pixel_width,
                                                src_pixel_height=src_pixel_height)
    # Display the ice
    _show_ice_grid(image_axes,
                   ice_grid,
                   proj,
                   new_extent,
                   ct_cmap,
                   ct_norm,
                   cfg.get('interpolation', 'nearest'))

    _add_median_extent_line(image_axes, data_proj, cfg)

    _add_polyline_overlays(image_axes, cfg)

    if cfg['image'].get('show_gridlines', True):
        _add_gridlines(image_axes, cfg)

    _add_colorbar(fig, ct_cmap, ct_norm, cfg)

    _add_rectangle_overlays(fig, cfg)

    _add_labels(image_axes, fig, cfg)

    _add_locations(image_axes, cfg['image']['locations'],
                   cfg['image']['locations_text_kwargs'],
                   cfg['image'].get('locations_path_effects', []))

    _add_legend(image_axes, cfg, 'missing_legend')
    _add_legend(image_axes, cfg, 'legend')

    _add_image_overlays(fig, cfg)

    _save_figure(cfg, fig)

    _run_imagemagick_convert(cfg)

    log.info('created {}'.format(cfg['output']))


def _add_rectangle_overlays(fig, cfg):
    for overlay in cfg.get('rectangle_overlays', []):
        ax = fig.add_subplot(1, 1, 1, gid=overlay.pop('id'))
        ax.axis('off')

        xy = overlay.pop('xy')
        width = overlay.pop('width')
        height = overlay.pop('height')

        ax.set_position(xy + [width, height])

        ax.add_patch(patches.Rectangle(xy, width, height, **overlay))


def _add_image_overlays(fig, cfg):
    for overlay in cfg.get('image_overlays', []):
        ax = fig.add_subplot(1, 1, 1, gid=overlay.pop('id'))
        ax.set_position(overlay['position'])
        ax.axis('off')

        if os.path.isabs(overlay['path']):
            img_path = overlay['path']
        else:
            img_path = os.path.join(os.path.dirname(cfg['config_filename']), overlay['path'])

        im = mpl.image.imread(img_path)

        # hack: copy the top row into another row on top of it; somehow the top
        # row is not being displayed
        im = np.concatenate((np.dstack(im[0, :, :].transpose()), im), axis=0)

        ax.imshow(im)


def _prepare_plate_carree_ice(cfg, hemi, data_proj,
                              image_proj, gridset, data_type):
    """Prepare ice data for a global Plate Carree image (google and sos)"""

    dst_bounds = cfg['projection']['bounds']
    dst_pixel_height = cfg['projection']['pixel_height']
    dst_pixel_width = cfg['projection']['pixel_width']

    src_pixel_height = cfg[hemi]['projection']['pixel_height']
    src_pixel_width = cfg[hemi]['projection']['pixel_width']
    src_bounds = cfg[hemi]['projection']['bounds']

    # pre-project the ice grid
    reproj, _ = util.reproj_ice_grid(gridset['data'], data_proj,
                                     src_bounds, image_proj,
                                     src_pixel_width=src_pixel_width,
                                     src_pixel_height=src_pixel_height,
                                     dst_pixel_width=dst_pixel_width,
                                     dst_pixel_height=dst_pixel_height,
                                     dst_size=cfg['canvas']['pixel_dims'],
                                     dst_bounds=dst_bounds,
                                     source_extra=0)

    reproj = _remove_land(reproj, cfg)
    # mask out the ocean
    reproj = np.ma.masked_where(reproj < 1, reproj)
    return reproj


def _create_global_ice_image(north_ice, south_ice, cfg):
    """Creates a global sea ice image for google and sos
    image types."""

    # Create a numpy array representing the RGBA image
    img_width, img_height = cfg['canvas']['pixel_dims']
    global_ice = np.ones((img_height, img_width, 4))

    # Create a new ice maask
    mask = np.logical_and(south_ice.mask, north_ice.mask)

    # Set the inverse of the new mask as the
    # alpha channel for the image (masked ice -> 0)
    global_ice[:, :, 3] = ~mask

    # Set non-ice to 0. If we don't do this,
    # Google Earth will make the ice edge
    # especially fuzzy because of
    # interpolation when wrapping the image
    # around the globe.
    global_ice[:, :, :-1][mask] = 0

    # Save the image.
    plt.imsave(cfg['output'], global_ice)
    log.info('created {}'.format(cfg['output']))


def make_plate_carree_image(cfg, data_type, north_gridset, south_gridset):
    """Creates images in the Plate Carree projection"""

    # Get the data's native projection
    N_proj = ccrs.Stereographic(**cfg['north']['projection']['ccrs'])
    S_proj = ccrs.Stereographic(**cfg['south']['projection']['ccrs'])

    image_proj = ccrs.PlateCarree()

    # Preapare the ice data.
    north_ice = _prepare_plate_carree_ice(cfg, 'north', N_proj,
                                          image_proj, north_gridset, data_type)
    south_ice = _prepare_plate_carree_ice(cfg, 'south', S_proj,
                                          image_proj, south_gridset, data_type)

    # Create the image
    _create_global_ice_image(north_ice, south_ice, cfg)


def _resize_mask(mask, shape):
    """If the mask isn't the same shape as the target shape, resize it to match."""
    return zoom(mask, np.divide(shape, mask.shape), order=0)


def _remove_land(grid_in, cfg):
    """Mask out land in the reprojected icegrid if a landmask in configured.

    In order to have a smooth appearance, these images are upsampled with
    bilinear interpolation.  As a side effect, in areas where ice is adjacent
    to land this regridding tends to smear ice onto the land.  In order to
    prevent sea ice from appearing atop land in the final images, we set all
    land values in the grid to 0 which has the effect of removing ice from
    land.

    The landmask configured should be land values computed by resampling of
    Boston University Version of Global 1 km Land Cover from MODIS 2001 to the
    native grid.  Landcover documation for EASE grids is here:
    http://nsidc.org/data/ease/ancillary.html and the same methods were
    followed for the science on a sphere grid (0.09degree).

    """
    grid = grid_in.copy()

    try:
        landmask = cfg['landmask']['filename']
        shape = cfg['landmask']['shape']
        ice_allowed_value = cfg['landmask']['ice_allowed_value']   # water locations.
        mask = np.fromfile(landmask, dtype=np.uint8).reshape(shape)
        mask = _resize_mask(mask, grid.shape)
        grid[mask != ice_allowed_value] = 0

    except KeyError as e:
        return grid_in
    except Exception as e:
        log.exception(e)
        return grid_in

    return grid
