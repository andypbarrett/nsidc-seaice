from unittest import TestCase

import seaice.nasateam as nt
from seaice.nasateam.loci_mask import _invalid_ice_mask_filename


class Test_InvalidIceMaskFilename(TestCase):
    def test_northern_hemisphere(self):
        expected = ('/projects/DATASETS/nsidc0622_valid_seaice_masks/'
                    'NIC_valid_ice_mask.N25km.09.1972-2007.nc')
        month = 9
        hemisphere = nt.NORTH

        actual = _invalid_ice_mask_filename(hemisphere, month)

        self.assertEqual(actual, expected)

    def test_southern_hemisphere(self):
        expected = '/share/data/seaice_index/ancillary/oceanmask.S03_v2.nc'
        month = 3
        hemisphere = nt.SOUTH

        actual = _invalid_ice_mask_filename(hemisphere, month)

        self.assertEqual(actual, expected)
