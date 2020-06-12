from .constants import NORTH_SHAPE, SOUTH_SHAPE
from . import valid_ice_masks as masks
from . import area_grids

NORTH = {
    'long_name': 'north',
    'short_name': 'N',
    'cols': NORTH_SHAPE[1],
    'rows': NORTH_SHAPE[0],
    'shape': NORTH_SHAPE,
    'valid_ice_mask_dir': masks.NORTH_VALID_ICE_MASK_DIR,
    'valid_ice_mask_variable_name': masks.NORTH_INVALID_ICE_MASK_VARIABLE_NAME,
    'mask': masks.NORTH_MASK,
    'grid_areas': area_grids.NORTH_AREA_GRID,
    'crs': 'EPSG:3411',

    # https://nsidc.org/data/polar-stereo/ps_grids.html
    # https://nsidc.org/data/atlas/epsg_3411.html
    'transformation_constants': {
        'scale_x': 25e3,
        'scale_y': -25e3,
        'offset_x': -3850e3,
        'offset_y': 5850e3,
        'theta': 0,
        'shearing_x': 0,
        'shearing_y': 0
    }
}

SOUTH = {
    'long_name': 'south',
    'short_name': 'S',
    'cols': SOUTH_SHAPE[1],
    'rows': SOUTH_SHAPE[0],
    'shape': SOUTH_SHAPE,
    'valid_ice_mask_dir': masks.SOUTH_VALID_ICE_MASK_DIR,
    'valid_ice_mask_variable_name': masks.SOUTH_INVALID_ICE_MASK_VARIABLE_NAME,
    'mask': masks.SOUTH_MASK,
    'grid_areas': area_grids.SOUTH_AREA_GRID,
    'crs': 'EPSG:3412',

    # https://nsidc.org/data/polar-stereo/ps_grids.html
    # https://nsidc.org/data/atlas/epsg_3412.html
    'transformation_constants': {
        'scale_x': 25e3,
        'scale_y': -25e3,
        'offset_x': -3950e3,
        'offset_y': 4350e3,
        'theta': 0,
        'shearing_x': 0,
        'shearing_y': 0
    }
}


def by_name(id):
    hemis = {'N': NORTH, 'S': SOUTH}
    return hemis.get(id[0].upper())
