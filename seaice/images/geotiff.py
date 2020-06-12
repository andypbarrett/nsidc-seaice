import logging
from matplotlib import colors
from osgeo import gdal, osr, gdal_array


log = logging.getLogger(__name__)


def make_geotiff(cfg, nt_hemi, gridset):
    """Makes a geotiff representation of a given gridset."""
    # Open a geotiff file for writing
    dataset, band = _create_geotiff(cfg, gridset)

    # Set the colortable
    if cfg['colortable'] is not None:
        _set_colortable(cfg, band)

    # Set the projection and geotransformation matrix.
    _set_projection(nt_hemi['crs'], dataset)
    _set_geotransform(cfg, dataset)

    # Flush the data to disk
    band.FlushCache()
    dataset.FlushCache()
    # Ensure the dataset is closed.
    dataset = None
    log.info('created {}'.format(cfg['output']))


def _create_geotiff(cfg, gridset):
    """Opens a geotiff image and writes the data in gridset

    Returns:
        - (dataset, band) tuple. `dataset` is the dataset returned from opening
            the geotiff with driver.Create(). Band is a gdal band object
            representing the first (and only) band in the dataset.
    """

    # Get the dataset's height and width
    height, width = gridset['data'].shape

    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(
        cfg['output'],
        width,
        height,
        1,
        _get_gdal_datatype(gridset['data'].dtype))

    band = dataset.GetRasterBand(1)
    band.WriteArray(gridset['data'])

    return dataset, band


def _get_gdal_datatype(np_datatype):
    """Takes a numpy datatype and returns the gdal type code"""
    return gdal_array.NumericTypeCodeToGDALTypeCode(np_datatype)


def _set_projection(crs, dataset):
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(crs[crs.find(':') + 1:]))

    dataset.SetProjection(srs.ExportToWkt())


def _set_geotransform(cfg, dataset):
    """Sets a gdal dataset's geotransform property"""
    # Get the pixel size
    pixel_height = cfg['projection']['pixel_height']
    pixel_width = cfg['projection']['pixel_width']

    # Get the upper-left corner (ulc) coordinates
    dataset_bounds = cfg['projection']['bounds']
    ulc = (dataset_bounds[0], dataset_bounds[-1])

    dataset.SetGeoTransform([ulc[0], pixel_width, 0, ulc[1], 0,
                             -pixel_height])


def _color_to_rgba(mpl_color):
    cc = colors.ColorConverter()
    mpl_rgb = cc.to_rgba(mpl_color)

    # Matplotlib returns a tuple of fractional values.
    # Get the 0-255 representation of the RGB tuple.
    rgb = tuple([int(255 * c) for c in mpl_rgb])

    # the last value, alpha, should be 0-1 instead of 0-255
    rgb = (*rgb[:3], rgb[3]/255)

    return rgb


def _get_cmap(cfg):
    colorbounds = cfg['colorbounds']
    colortable = cfg['colortable']

    cmap, norm = colors.from_levels_and_colors(colorbounds, colortable)

    gdal_cmap = {}
    for i in range(int(min(colorbounds)), int(max(colorbounds)) + 1):
        gdal_cmap[i] = _color_to_rgba(cmap(norm(i)))

    return gdal_cmap


def _set_colortable(cfg, band):
    c = gdal.ColorTable()
    cmap = _get_cmap(cfg)

    # `color` is a 4-tuple containing r, g, b, alpha; gdal doesn't want the
    # alpha
    for val, color in cmap.items():
        c.SetColorEntry(val, color[:3])

    band.SetColorTable(c)
