from . import common
from . import geom
from . import grids


def daily_median(config):
    """Create a polyline shapefile for the climatological median daily sea ice
    extent.

    Returns a tuple containg the shapely MultiLineString that is drawn in the
    shapefile, and the path to the created .zip file.

    Arguments
    ---------
    config: dictionary of settings from command-line

    """
    grid = grids.grid(config)

    config['smoothing'] = True
    multilinestring = geom.multilinestring_from_grid(grid, config)

    common._create_shapefile(config, multilinestring)
