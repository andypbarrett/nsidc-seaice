from . import common
from . import geom
from . import grids


def monthly_polygon(config):
    """Create a polygon shapefile for monthly sea ice extent.

    Returns a tuple containing a list of the shapely geometry objects drawn in
    the shapefile, and the path to the created .zip file.

    Arguments
    ---------
    config: dictionary of settings from command-line

    """
    grid = grids.grid(config, keep_flag_values=False)

    multipolygon = geom.multipolygon_from_grid(grid, config)

    common._create_shapefile(config, *multipolygon.geoms)
