from . import common
from . import geom
from . import grids


def monthly_polyline(config):
    """Create a polyline shapefile for monthly sea ice extent.

    Returns a tuple containing the shapely MultiLineString that is drawn in the
    shapefile, and the path to the created .zip file.

    Arguments
    ---------
    config: dictionary of settings from command-line

    """

    grid = grids.grid(config, treat_coast_as_land=True)

    multilinestring = geom.multilinestring_from_grid(grid, config)

    common._create_shapefile(config, multilinestring)
