import os

import numpy as np

from .constants import NORTH_SHAPE, SOUTH_SHAPE

GRID_AREA_SCALE = 1000

# Area Grids were added to project from:
# /projects/DATASETS/brightness-temperatures/polar-stereo/tools/geo-coord/grid

mask_dir = os.path.join(os.path.dirname(__file__), 'pkg_data', 'area_grids')
NORTH_AREA_GRID_FILENAME = os.path.join(mask_dir, 'psn25area_v3.dat')
SOUTH_AREA_GRID_FILENAME = os.path.join(mask_dir, 'pss25area_v3.dat')


NORTH_AREA_GRID = np.fromfile(NORTH_AREA_GRID_FILENAME,
                              dtype=np.uint32).reshape(*NORTH_SHAPE) / GRID_AREA_SCALE


SOUTH_AREA_GRID = np.fromfile(SOUTH_AREA_GRID_FILENAME,
                              dtype=np.uint32).reshape(*SOUTH_SHAPE) / GRID_AREA_SCALE
