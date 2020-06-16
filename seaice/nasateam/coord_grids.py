import os

import numpy as np

from .constants import NORTH_SHAPE, SOUTH_SHAPE

GRID_COORD_SCALE = 100000.

# Coord Grids were added to project from:
# ftp://sidads.colorado.edu/pub/DATASETS/seaice/polar-stereo/tools/

mask_dir = os.path.join(os.path.dirname(__file__), 'pkg_data', 'coord_grids')
NORTH_LAT_GRID_FILENAME = os.path.join(mask_dir, 'psn25lats_v3.dat')
NORTH_LON_GRID_FILENAME = os.path.join(mask_dir, 'psn25lons_v3.dat')
SOUTH_LAT_GRID_FILENAME = os.path.join(mask_dir, 'pss25lats_v3.dat')
SOUTH_LON_GRID_FILENAME = os.path.join(mask_dir, 'pss25lons_v3.dat')


NORTH_LAT_GRID = np.fromfile(NORTH_LAT_GRID_FILENAME,
                             dtype=np.int32).reshape(*NORTH_SHAPE) / GRID_COORD_SCALE
NORTH_LON_GRID = np.fromfile(NORTH_LON_GRID_FILENAME,
                              dtype=np.int32).reshape(*NORTH_SHAPE) / GRID_COORD_SCALE

SOUTH_LAT_GRID = np.fromfile(SOUTH_LAT_GRID_FILENAME,
                              dtype=np.int32).reshape(*SOUTH_SHAPE) / GRID_COORD_SCALE
SOUTH_LON_GRID = np.fromfile(SOUTH_LON_GRID_FILENAME,
                              dtype=np.int32).reshape(*SOUTH_SHAPE) / GRID_COORD_SCALE
