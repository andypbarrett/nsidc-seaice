import logging

import numpy as np

from .errors import SeaIceDataTypeError


log = logging.getLogger(__name__)


def concentration_cutoff(cutoff, grid):
    if type(grid) is np.ndarray:
        where = np.where
    elif type(grid) is np.ma.MaskedArray:
        where = np.ma.where
    else:
        log.error('{}, {}'.format(cutoff, grid))
        raise SeaIceDataTypeError('grid has unexpected type')

    grid = where(grid < cutoff, 0, grid)

    return grid
