import os

from .constants import SEA_ICE_BASE_DIR

BLUE_MARBLE_PICKLE_DIR = os.path.join(SEA_ICE_BASE_DIR, 'cache/')
BLUE_MARBLE_PICKLE_PATH = os.path.join(BLUE_MARBLE_PICKLE_DIR,
                                       'reprojected_blue_marble_{hemi}.p')
