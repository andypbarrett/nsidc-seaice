from rasterio import features
from shapely import geometry
import numpy as np
import pandas as pd

from . import common


PIXEL_SIZE = 25e3  # each pixel in polar stereographic north is 25,000 meters
MIN_PIXELS = 7  # minimum length, in pixels, of lines to draw


def multilinestring_from_grid(grid, config):
    """Returns a Shapely MultiLineString Geometry object containing polylines
    for the ice extent in the given grid. The ice is contoured such that the
    lines only trace the ice where it borders the ocean, not where it borders
    land.

    Arguments
    ---------
    grid: numpy array containining 1s and 0s representing ice extent, as well as
        possible flag values over 250.

    config: configuration dict containing a hemi, being nt.NORTH or nt.SOUTH;
        and smoothing, a bool describing whether the resulting polylines should
        be smoothed by averaging their coordinates with neighboring
        coordinates--this should only be used for creating median polylines.

    """

    transform = _affine_transform_matrix(**config['hemi']['transformation_constants'])

    def contour(grid):
        """"Contour the features in a grid; returns a Shapely GeometryCollection for the
        given grid.

        """
        multi_line_strings = []
        for shape, value in features.shapes(grid, transform=transform):
            if value:
                coords = shape['coordinates']
                multi_line_string = geometry.MultiLineString(coords)
                multi_line_strings.append(multi_line_string)

        return geometry.collection.GeometryCollection(multi_line_strings)

    land_ice_grid = _feature_grid(grid, common.LAND, common.ICE)
    land_ice_contour = contour(land_ice_grid)

    land_grid = _feature_grid(grid, common.LAND)
    land_contour = contour(land_grid)

    ice_lines = land_ice_contour.difference(land_contour)

    def smooth(line_string):
        if config.get('smoothing', False):
            return _smooth_line(line_string)
        else:
            return line_string

    if type(ice_lines) is geometry.MultiLineString:
        min_length = PIXEL_SIZE * MIN_PIXELS
        geoms = [smooth(geom) for geom in ice_lines.geoms if geom.length >= min_length]
        ice_lines = geometry.MultiLineString(geoms)

    elif type(ice_lines) is geometry.LineString:
        ice_lines = smooth(ice_lines)
        ice_lines = geometry.MultiLineString(([(x, y) for x, y in ice_lines.coords],))

    return ice_lines


def multipolygon_from_grid(grid, config):
    transform = _affine_transform_matrix(**config['hemi']['transformation_constants'])

    polygons = []
    for shape, value in features.shapes(grid, transform=transform):
        if value:
            coords = shape['coordinates']
            polygon = geometry.Polygon(coords[0], coords[1:])
            polygons.append(polygon)

    return geometry.MultiPolygon(polygons)


# https://trac.osgeo.org/postgis/wiki/DevWikiAffineParameters
def _affine_transform_matrix(scale_x=None,
                             scale_y=None,
                             offset_x=None,
                             offset_y=None,
                             theta=None,
                             shearing_x=None,
                             shearing_y=None):
    """Returns a 6-tuple representing the 2x3 affine transform matrix calculated
    from the input parameters.

    Arguments
    ---------
    scale_x: scale factor in x direction
    scale_y: scale factor in y direction
    offset_x: offset in x direction
    offset_y: offset in y direction
    theta: angle of rotation clockwise around origin (radians)
    shearing_x: shearing parallel to x axis
    shearing_y: shearing parallel to y axis

    """
    a_11 = scale_x * ((1 + (shearing_x * shearing_y)) * np.cos(theta) + shearing_y * np.sin(theta))
    a_12 = scale_x * (shearing_x * np.cos(theta) + np.sin(theta))
    a_13 = offset_x
    a_21 = scale_y * (-(1 + shearing_x * shearing_y) * np.sin(theta) + shearing_y * np.cos(theta))
    a_22 = scale_y * (-shearing_x * np.sin(theta) + np.cos(theta))
    a_23 = offset_y

    return (a_11, a_12, a_13, a_21, a_22, a_23)


def _feature_grid(grid, *values):
        """Return a grid for a feature defined by values; in the returned grid, a value
        of 1 indicates that a gridcell's value in the input grid was one of the
        given values; other gridcells have a value of 0.

        """
        return np.in1d(grid, values).reshape(grid.shape).astype('int16')


def _smooth_line(line_string, window=3):
    df = pd.DataFrame(list(line_string.coords))
    df_smoothed = df.rolling(center=True, window=window, min_periods=0).mean()
    coords_list = [tuple(val) for val in df_smoothed.values]
    return geometry.LineString(coords_list)
