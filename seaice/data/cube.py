import numpy as np


def average_cube(cube):
    """ average 3D numpy array along z axis """
    return np.ma.mean(cube, axis=2)


def apply_patch(grid, patch):
    """Replace masked areas in grid with values from patch."""
    if np.any(grid.mask):
        grid = np.ma.where(grid.mask, patch, grid)

    return grid
