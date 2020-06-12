from netCDF4 import Dataset

from enum import Enum
import numpy as np
import os

from scipy.ndimage.morphology import binary_dilation


class Loci(Enum):
    ocean = 0
    valid_ice = 1
    coast = 2
    land = 3
    lake = 4
    shore = 5
    near_shore = 6
    off_shore = 7


def shore_mask(hemisphere):
    """Return mask of landlike, shore, near-shore and off-shore gridcells.

    landlike   = land, coast, or lake (revalued as Loci.land)
    shore      = 1 gridcell from landlike (Loci.shore)
    near_shore = 2 gridcells from landlike (Loci.near_shore)
    off_shore  = 3 gridcells from landlike (Loci.off_shore)
    """

    # Structuring elements used in binary_dilation. They are pulled from
    # IDL, but they match exactly the elements used by default in pmalgos
    # that are located at /share/data/pmalgos/spillover_kernels

    shore_struct = np.array([[1, 1, 1],
                             [1, 1, 1],
                             [1, 1, 1]])

    near_shore_struct = np.array([[0, 1, 1, 1, 0],
                                  [1, 1, 1, 1, 1],
                                  [1, 1, 1, 1, 1],
                                  [1, 1, 1, 1, 1],
                                  [0, 1, 1, 1, 0]])

    off_shore_struct = np.array([[0, 0, 1, 1, 1, 0, 0],
                                 [0, 1, 1, 1, 1, 1, 0],
                                 [1, 1, 1, 1, 1, 1, 1],
                                 [1, 1, 1, 1, 1, 1, 1],
                                 [1, 1, 1, 1, 1, 1, 1],
                                 [0, 1, 1, 1, 1, 1, 0],
                                 [0, 0, 1, 1, 1, 0, 0]])

    any_month_will_do = 1
    loci = loci_mask(hemisphere, any_month_will_do)
    shore_mask = np.zeros_like(loci)

    shore_mask[(loci == Loci.land.value) |
               (loci == Loci.coast.value) |
               (loci == Loci.lake.value)] = 1

    landlike = shore_mask.copy()

    shore = binary_dilation(landlike, structure=shore_struct, iterations=1)
    near_shore = binary_dilation(landlike, structure=near_shore_struct, iterations=1)
    off_shore = binary_dilation(landlike, structure=off_shore_struct, iterations=1)

    shore_mask[off_shore == 1] = Loci.off_shore.value
    shore_mask[near_shore == 1] = Loci.near_shore.value
    shore_mask[shore == 1] = Loci.shore.value
    shore_mask[landlike == 1] = Loci.land.value

    return shore_mask


def loci_mask(hemisphere, month):
    """Returns the 'Land Ocean Coast Ice' mask for the desired hemisphere and month.
    the returned masked is a numpy array with values enumerated

    """
    ice_mask_dataset = Dataset(_invalid_ice_mask_filename(hemisphere, month), 'r')
    mask = ice_mask_dataset.variables[hemisphere['valid_ice_mask_variable_name']][:]
    return mask


def invalid_ice_mask(hemisphere, month):
    """Returns the invalid ice mask for the given hemisphere and month, taken from
    NSIDC-0622. The returned mask is a 2D numpy boolean array, where True values
    indicate that valid ice cannot occur at that gridcell.

    Positional Arguments:
    ---------------------
    hemisphere: nt.NORTH or nt.SOUTH

    month: integer representing the month

    """
    mask = loci_mask(hemisphere, month)
    invalid_ice_mask = mask != hemisphere['mask']['valid_ice']
    return invalid_ice_mask


def _invalid_ice_mask_filename(hemisphere, month):

    if hemisphere['short_name'].upper() == 'N':
        mask_filename = os.path.join(
            '{dir_}'.format(dir_=hemisphere['valid_ice_mask_dir']),
            'NIC_valid_ice_mask.N25km.{month:02}.1972-2007.nc'.format(month=month))
    elif hemisphere['short_name'].upper() == 'S':
        mask_filename = os.path.join(
            '{dir_}'.format(dir_=hemisphere['valid_ice_mask_dir']),
            'oceanmask.S{month:02}_v2.nc'.format(month=month))
    else:
        raise ValueError('Invalid hemisphere short_name')

    return mask_filename
