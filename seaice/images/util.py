import logging
import os
import pickle

import cartopy.crs as ccrs
import numpy as np
import rasterio
from rasterio.crs import CRS as rcrs
from rasterio import warp

from seaice.logging import log_duration
import seaice.nasateam as nt

log = logging.getLogger(__name__)


def _calculate_reproj_params(src_crs, src_width, src_height,
                             src_bounds, dst_crs):
    """Returns reprojection parameters used by rasterio

    Arguments
    ---------
        src_crs - the source dataset's rasterio crs object.

        src_width - The source dataset's width in number of
        pixels.

        src_height - THe source dataset's height in number
        of pixels.

        src_bounds - The outer bounds of the source dataset in
        the source projection's coordinates. Should be
        given as a [L, R, B, T] list.

        dst_crs - The rasterio crs object representing the
        coordinate system to reproject to.

    Returns
    -------
        (rasterio affine transformation,
         destination image width,
         destination image height)
     """
    left, right, bottom, top = src_bounds

    return warp.calculate_default_transform(
        src_crs, dst_crs, src_width,
        src_height, left, bottom,
        right, top)


def _get_affine_transform(bounds, pixel_width, pixel_height=None):
    """Gets a rasterio affine transformation object from the given
    bounds and pixel size. Assumes zero image rotation.

    Arguments:
    ---------
        bounds - The outer bounds of the image as a [L, R, B, T] array

        pixel_width - The size of the image pixel's width in the
        dataset's current coordinate system's units of measurement.

        pixel_height - Optional. The size of the image pixel's height in
        the dataset's current coordinate system's units of measurement.
        If none given, assume square pixels by using the value of pixel_width.

    Returns:
        Rasterio affine transformation (pixel_width, 0, left, 0, pixel_height, top)
        object.
    """
    if pixel_height is None:
        pixel_height = pixel_width

    left, _, _, top = bounds
    transform = rasterio.Affine(pixel_width,    # w-e pixel size
                                0,              # row rotation
                                left,      # left
                                0,              # column rotation
                                -pixel_height,  # n-s pixel size
                                top)     # top

    return transform


def _compute_new_bounds(width, height, transform=None, pixel_width=None,
                        pixel_height=None, left=None, top=None):
    """Computes new bounds for an image based on a rasterio
    affine transformation object and the width/height of the image

    Arguments
    ---------
        width - the image's width in number of pixels

        height - the image's height in number of pixels

        transform - The rasterio affine transformation object for the
        given image. If this is given the pixel_width, pixel_height,
        left, and top arguments are not required.

        pixel_width - The size of the image pixel's width in the
        dataset's current coordinate system's units of measurement.

        pixel_height - Optional. The size of the image pixel's height in
        the dataset's current coordinate system's units of measurement.
        If none given, assume square pixels by using the value of pixel_width.

        left - The western bound of the dataset.

        top - The northern bound of the dataset.

    Returns
    -------
        A [L, R, B, T] bounds list for the dataset.

    """
    if transform is not None:
        left = transform[2]
        top = transform[5]
        pixel_width = transform[0]
        pixel_height = transform[4]
    else:
        required_args = {'pixel_width': pixel_width, 'left': left, 'top': top}
        missing = [key for key, var in required_args.items() if var is None]
        if missing:
            raise ValueError('{} are required arguments if transform is None.'.format(missing))

        if pixel_height is None:
            # Assume square pixels
            pixel_height = -pixel_width
        else:
            pixel_height = -pixel_height

    return [left,
            left + pixel_width * width,
            top + pixel_height * height,
            top]


def _reproj_grid(src_grid, src_crs, src_transform,
                 dst_crs, dst_width, dst_height,
                 dst_transform, source_extra=60):
    """Reprojects a given numpy array (src_grid) into
    the destination crs, given the provided parameters.

    Arguments
    ---------
        src_grid: A numpy array representing an image to be
        reprojected. This array may have a shape of
        (num_layers, height, width) for RGB or other
        multi-band images.

        src_crs: A rasterio crs object representing the
        current coordinate reference system of the src_grid

        src_transform: Rasterio affine transformation object
        for the source dataset. See http://bit.ly/2gxf4Bu and
        http://bit.ly/2gHYphS for more information about
        affine transformations.

        dst_crs: A rasterio crs object representing the
        coodinate reference system into which the image
        will be projected.

        dst_width: The number of pixels wide the resulting
        image wil be.

        dst_height:The number of pixels high the resulting
        image wil be.

        dst_transform: Rasterio affine transformation object
        for the destination dataset.See http://bit.ly/2gxf4Bu and
        http://bit.ly/2gHYphS for more information about
        affine transformations.

        source_extra: This is a number of extra pixels added around
        the source window for a given request. Setting this larger will
        increase the amount of data that needs to be read, but can avoid
        missing source data (http://bit.ly/2eG3IKJ)
    Returns
    -------
        A reprojected grid of the input src_grid.

    """
    # Determine if this is a multi-band image
    # (e.g., blue marble is a 3 band RGB image)
    try:
        layers, _, _ = src_grid.shape
    except ValueError:
        layers = 1

    # Create an output data structure with the destination's
    # size
    dest_array = np.empty((dst_height, dst_width))

    # Determine if the image is a masked array.
    masked = type(src_grid) is np.ma.core.MaskedArray

    if masked:
        # If so, treat the mask as another data layer.
        layers += 1
        src_data = np.stack((src_grid.data, src_grid.mask))
    else:
        src_data = src_grid

    if layers == 1:
        # If this is not a multi-band or masked image,
        # Make the source and destination data objects
        # iterable
        dst_data = (dest_array, )
        src_data = (src_grid, )
    else:
        # Make the destination array appropriately sized
        dst_data = np.stack((dest_array,) * layers)

    # Reproject each layer of the image
    for src, dst in zip(src_data, dst_data):
        # See http://bit.ly/2hJPsSS for documentation
        # on rasterio's warp.reproject
        warp.reproject(
            source=src.astype(float),
            src_crs=src_crs,
            src_nodata=np.nan,
            src_transform=src_transform,
            destination=dst,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,
            SOURCE_EXTRA=source_extra,
            resampling=warp.Resampling.nearest)

    # If the data were masked, create a new masked_array
    if masked:
        dst_data = np.ma.masked_array(np.squeeze(dst_data[:-1]),
                                      mask=dst_data[-1].astype(bool))
    elif layers == 1:
        # Just return the data, not the
        # tuple-enclosed iterable version
        dst_data = dst_data[0]

    return dst_data


class BlueMarbleProj(ccrs.Projection):
    """Custom projection for blue marble images. Parameters default to
    northern hemisphere.

    Arguments:
    ---------
        satellite_height: perspective height above the earth that the 'satellite'
        is viewing from.

        center_lat: The latitude that will be placed at the center of the map's geo-axes

        center_lon: The longitude that will be placed at the center of the map's geo-axes

        x_lims: The x limits (min, max) of the projection. The default can be used for
        both north and south blue marble images. The default was obtained by adding
        a pixel's worth of space in projected coordinates (1920.54) to each side of the
        maximum projected bounds of the blue marble image.

        y_lims: The y limits (min, max) of the projection. The default can be used for
        both north and south blue marble images. The default was obtained by adding
        a pixel's worth of space in projected coordinates (1920.54) to the top and bottom of the
        maximum projected bounds of the blue marble image.

    Note:
    -----
        - It appears that version >0.14 of cartopy will natively support this projection
        as 'NearsidePerspective'

        - The default max_x and max_y are values obtained from projecting the blue-marble image
        and then looking at it's max x/y. Cartopy needs these values because it determines
        the size and shape of the projected space.
    """
    def __init__(self, satellite_height=9000000.0,
                 central_latitude=78.0, central_longitude=-45.0,
                 x_lims=(-4098880.759621147, 4098002.0879747514),
                 y_lims=(-4104056.811265956, 4104157.247400926)):

        proj4_params = [
             ('h', satellite_height),
             ('lat_0', central_latitude),
             ('lon_0', central_longitude),
             ('proj', 'nsper'),
             ('units', 'm'),
             ('x_0', 0),
             ('y_0', 0)
        ]
        super(BlueMarbleProj, self).__init__(proj4_params, globe=None)

        # Set the semimajor and semiminor axes to be
        # half the distance across the image
        x_radius = (abs(x_lims[0]) + abs(x_lims[1])) / 2
        y_radius = (abs(y_lims[0]) + abs(y_lims[1])) / 2
        semimajor = max(x_radius, y_radius)
        semiminor = min(x_radius, y_radius)

        # Create the projection's boundary.
        coords = ccrs._ellipse_boundary(semimajor, semiminor,
                                        0, 0, 61)
        self._boundary = ccrs.sgeom.LinearRing(coords.T)

        self._xlim = x_lims
        self._ylim = y_lims
        self._threshold = np.diff(self._xlim)[0] * 0.02

    @property
    def boundary(self):
        return self._boundary

    @property
    def threshold(self):
        return self._threshold

    @property
    def x_limits(self):
        return self._xlim

    @property
    def y_limits(self):
        return self._ylim


def reproject_bm_image(dataset, cfg, proj, pickle_path=None):
    """Reproject a blue marble image from its native coordinate system
    to the given desination projection.

    Arguments:
    ---------
        dataset - A 3D numpy array representing a blue-marble
        image read from disk using rasterio. This array has a size
        of (3, image_height, image_width), where 3 is the number of bands
        (Red, Green, Blue). E.g., the red channel is represented by
        dataset[0, :, :].

        cfg - A valid cfg object

        proj - A cartopy projection object representing the projection
        to transform the blue marble image into.

        pickle_path - If given, attempt to load the reprojected blue marble from
        this location; if nothing is found, save the calculated reprojection at
        this path.

    Returns:
    -------
        A (image, bounds) tuple.

        Image is an RGB image represented by a 3D numpy float array with a size
        of (image_height, image_width, 3), where 3 is the number of color channels
        (Red, Green, and Blue). E.g., the red channel is represented by Image[:, :, 0].
        Areas that could not be projected (e.g., outside the bounds of the coordinate
        system being projected to) are set to np.nan.

        Bounds is a list representing the projected outer bounds [L, R, B, T] of the
        returned image.

    """
    if pickle_path is None:
        pickle_path = cfg.get('pickle_path',
                              nt.BLUE_MARBLE_PICKLE_PATH).format(hemi=cfg['hemisphere'])

    if _reprojection_is_saved(pickle_path, dataset, cfg, proj):
        log.debug('Begin: Loading reprojected blue marble from {}'.format(pickle_path))
        return_package = pickle.load(open(pickle_path, 'rb'))['output']
        log.debug('Finished: Loading reprojected blue marble from {}'.format(pickle_path))
        return return_package

    log.debug('Reprojecting blue marble...')

    # bm_bounds is a list [L,R,B,T]
    bm_bounds = cfg['blue_marble_image']['projection']['bounds']
    bm_pixel_size = cfg['blue_marble_image']['pixel_size']

    dst_crs = rcrs({**proj.proj4_params, **{'wktext': True}})
    src_crs = rcrs.from_epsg(4326)

    # Rasterio works with an affine transformation matrix.
    # Let it create what it needs from a standard gdal geotranformation
    # matrix
    source_transform = _get_affine_transform(bm_bounds, bm_pixel_size)

    # Calc the ideal dimensions/transform for the projected image.
    # This process attempts to create a valid transformation for all
    # pixels in the input (global) blue marble image. Because the desired
    # projection does not make every region of the earth visible,
    # not all pixels can be mapped (e.g., in the projection for the
    # northern hemisphere, Australia is not visible, and GDAL
    # encounters an error when trying to reproject Australia's pixels
    # from the input image). Although the resulting tranformation is
    # sufficient for creating the desired image, GDAL produces errors to
    # warn the user of an incomplete transformation. Indicate to users that
    # this is expected with INFO level log messages.
    dataset_width = dataset.shape[2]
    dataset_height = dataset.shape[1]
    log.info('GDAL errors logged after this message that indicate tolerance '
             'condition errors and that the reprojection failed '
             'can be safely ignored.')
    ideal_transform = _calculate_reproj_params(src_crs, dataset_width,
                                               dataset_height, bm_bounds,
                                               dst_crs)
    log.info('There are no other expected GDAL errors after this message.')
    dst_affine, dst_width, dst_height = ideal_transform

    # Calculate the projected bounds of the data. Matplotlib will use this.
    projected_bounds = _compute_new_bounds(dst_width, dst_height, transform=dst_affine)

    # Do the actual reprojection
    dest_array = _reproj_grid(dataset, src_crs, source_transform,
                              dst_crs, dst_width, dst_height,
                              dst_affine, source_extra=160)
    dest_array = np.rollaxis(dest_array, 0, 3)

    log.debug('Done reprojecting blue marble')

    output = (dest_array, projected_bounds)
    _save_reprojection(pickle_path, dataset, cfg, proj, output)

    return output


# does the 'input' portion of the pickled projection info match the current
# input parameters? (this is kind of like memoizing/lru_cache)
def _reprojection_is_saved(pickle_path, dataset, cfg, proj):
    try:
        saved = pickle.load(open(pickle_path, 'rb'))
        return saved['input'] == _reprojection_input_dict(dataset, cfg, proj)

    except FileNotFoundError:
        return False


# save the computed results, along with some of the input info used to make
# those computations
def _save_reprojection(pickle_path, dataset, cfg, proj, output):
    obj = {'input': _reprojection_input_dict(dataset, cfg, proj),
           'output': output}

    try:
        pickle.dump(obj, open(pickle_path, 'wb'))
        log.info('wrote {}'.format(os.path.realpath(pickle_path)))

    except FileNotFoundError as e:
        log.error('Could not write pickle_path {path}; {e}'.format(
            path=os.path.realpath(pickle_path), e=e))


# starting from the input params to reproject_bm_image(), what are some values
# relevant to the reprojection? we need to make sure the pickled output is
# always valid for the given input
def _reprojection_input_dict(dataset, cfg, proj):
    return {
        'dataset_shape': dataset.shape,
        'bm_dir': cfg['blue_marble_image']['bm_dir'],
        'bm_filename': cfg['blue_marble_image']['bm_filename'],
        'bounds': cfg['blue_marble_image']['projection']['bounds'],
        'central_latitude': cfg['blue_marble_image']['projection']['ccrs']['central_latitude'],
        'pixel_size': cfg['blue_marble_image']['pixel_size'],
        'proj': proj.proj4_init
    }


def scale_image(img, out_min, out_max, data_min=None, data_max=None):
    """Scales an image's (np.ndarray) input values to out_min-out_max

    Arguments:
    ---------
        img: A 3d numpy array representing an RGB image, where
        the red channel is represented by img[:, :, 0]

        out_min: Scale the data between this and out_max. Defaults to 0.

        out_max: Scale the data between out_min and this. Defaults to 255.

        data_min: Defaults to the img's minimum value. Any value in the img
        lower than this value is set to data_min

        data_max: Defaults to the img's maximum value. Any value in the img
        greater than this value is set to data_max.

    Returns:
    -------
        A numpy array with the same shape as the input img, scaled between out_min
        and out_max.
    """

    out_img = np.zeros_like(img)

    data_min = data_min or img.min()
    data_max = data_max or img.max()

    img = np.clip(img, data_min, data_max)

    scalar = ((out_min * data_max) - (out_max * data_min)) / (data_max - data_min)
    norm = (out_max - out_min) / (data_max - data_min)

    out_img = img * norm + scalar

    return out_img


@log_duration(log, 'DEBUG')
def apply_gamma(img, out_min=0, out_max=255, gamma=1, data_min=None, data_max=None):
    """Applys a gamma transformation to the input image's
    (np.ndarray) brightness values

    Arguments:
    ----------
        img: A 3d numpy array representing an RGB image, where
        the red channel is represented by img[:, :, 0]

        out_min: Scale the data between this and out_max. Defaults to 0.

        out_max: Scale the data between out_min and this. Defaults to 255.

        gamma: Gamma value to apply to the image.

        data_min: Defaults to the img's minimum value. Any value in the img
        lower than this value is set to data_min

        data_max: Defaults to the img's maximum value. Any value in the img
        greater than this value is set to data_max.

    Returns:
    -------
        A gamma adjusted numpy array with the same shape as the input img.

    """
    scaled = scale_image(img, 0, 1, data_min=data_min, data_max=data_max)
    return scale_image(scaled ** gamma, out_min, out_max,
                       data_min=0, data_max=1)


def mask_bm_image(img):
    """Masks a reprojected blue marble image by making
    areas marked with np.nan (from reprojection) have
    full transparency. This adds an alpha channel to
    the image, resulting in an RGBA image.
    """
    mask = np.empty(img.shape[:-1])

    mask = ~np.isnan(img[:, :, 0])
    mask = mask.astype(int)

    new_img = np.dstack((img, mask))
    return new_img


def reproj_ice_grid(ice_grid, src_proj, src_bounds,
                    dst_proj, src_pixel_width, src_pixel_height,
                    dst_pixel_width=None, dst_pixel_height=None,
                    dst_size=None, dst_bounds=None, source_extra=60):
    """Reprojects the given ice grid from the src_proj
    to the dst_proj

    Arguments
    ---------
        ice_grid - A 2D numpy array representing a standard ice grid.

        src_proj - Cartopy crs object representing the ice_grid's projection

        src_bounds - The outer bounds of the ice_grid, in projected coordinates. [L, R, B, T].

        dst_proj - Cartopy crs object representing the destination coordinate system.

        src_pixel_wdith - The east-west size of the source image's pixels in projected
        coodinate system units

        src_pixel_height - The north-south size of the source image's pixels in projected
        coodinate system units

        dst_pixel_width - The east-west size of the reprojected image's pixels,
        in projected coodinate system units. dst_size and dst_bounds must not
        be set if this argument is to be used.

        dst_pixel_height - The north-south size of the reprojected image's pixels,
        in projected coodinate system units. The value of dst_pixel_width will be
        used if dst_pixel_height is not given. dst_size and dst_bounds must not
        be set if this argument is to be used.

        dst_size - Tuple representing the size of the reprojected ice grid (width, height)
        in pixels. dst_bounds must also be given if this is provided.

        dst_bounds - The outer bounds of the of the newly projected image [L, R, B, T].
        dst_size must also be given if this is provided.

        source_extra - This is a number of extra pixels added around
        the source window for a given request. Setting this larger will
        increase the amount of data that needs to be read, but can avoid
        missing source data (http://bit.ly/2eG3IKJ)

    Returns
    -------
        A (image, bounds) tuple containing a reprojected numpy array and that array's bounds
        in projected coordinates.
    """
    # If not all required optional arguments are set, warn the user.
    optional_args = {'dst_pixel_width': dst_pixel_width,
                     'dst_size': dst_size,
                     'dst_bounds': dst_bounds}
    unset_options = [key for key, val in optional_args.items() if val is None]
    set_options = [key for key, val in optional_args.items() if val is not None]
    if set_options and unset_options:
        log.warn('{} arguments must also be set if {} are to set'.format(unset_options,
                                                                         set_options))

    # Get rasterio crs objects it needs for reprojection
    # From the cartopy representations.
    dst_crs = rcrs({**dst_proj.proj4_params, **{'wktext': True}})
    src_crs = rcrs.from_string(src_proj.proj4_init)

    src_height, src_width = ice_grid.shape

    # Create the destination transformation
    # Create an optional_args var that is tru or false dependening on below.
    if unset_options:
        # Get the ideal transformation paramters
        ideal_transform = _calculate_reproj_params(src_crs, src_width,
                                                   src_height, src_bounds,
                                                   dst_crs)

        dst_transform, dst_width, dst_height = ideal_transform

        if dst_bounds is None:
            dst_bounds = _compute_new_bounds(dst_width, dst_height,
                                             transform=dst_transform)

    else:
        dst_width, dst_height = dst_size
        dst_transform = _get_affine_transform(dst_bounds, dst_pixel_width, dst_pixel_height)

    # Create the source transformation
    src_transform = _get_affine_transform(src_bounds, src_pixel_width, src_pixel_height)

    # Do the reprojection
    new_ice = _reproj_grid(ice_grid, src_crs, src_transform,
                           dst_crs, dst_width, dst_height,
                           dst_transform, source_extra=source_extra)

    return new_ice, dst_bounds
