# Information about the default locations of valid ice mask data


NORTH_VALID_ICE_MASK_DIR = '/projects/DATASETS/nsidc0622_valid_seaice_masks/'
NORTH_INVALID_ICE_MASK_VARIABLE_NAME = 'valid_ice_flag'
NORTH_MASK = {
    'ocean': 0,
    'valid_ice': 1,
    'coast': 2,
    'land': 3,
    'lake': 4
}

SOUTH_VALID_ICE_MASK_DIR = '/share/data/seaice_index/ancillary'
SOUTH_INVALID_ICE_MASK_VARIABLE_NAME = 'oceanmask'
SOUTH_MASK = {
    'ocean': 0,    # OPEN_WATER
    'valid_ice': 1,   # POSSIBLE_ICE
    'coast': 2,
    'land': 3,
    'lake': 4
}
