import numpy as np
import numpy.testing as npt
import unittest
from unittest.mock import patch

from ..image import _remove_land

LAND = 200
OCEAN = 3
ICE = 1
ZERO = 0


class Test__remove_land(unittest.TestCase):

    landmask = np.array([[LAND, OCEAN, OCEAN],
                         [LAND, OCEAN, OCEAN],
                         [OCEAN, OCEAN, OCEAN]])

    @patch('seaice.images.image.np.fromfile')
    def test_replaces_ice_with_0(self, mock_fromfile):

        mock_fromfile.return_value = self.landmask

        cfg = {
            'landmask': {
                'filename': 'mask_filename',
                'shape': (3, 3),
                'ice_allowed_value': OCEAN}
        }

        ice = np.array([[ICE, ICE, ICE],
                        [ZERO, ICE, ICE],
                        [ZERO, ICE, ICE]])

        expected = np.array([[ZERO, ICE, ICE],
                             [ZERO, ICE, ICE],
                             [ZERO, ICE, ICE]])

        actual = _remove_land(ice, cfg)
        npt.assert_array_equal(expected, actual)

    def test_returns_input_grid_when_no_landmask_configured(self):

        cfg = {}
        ice = np.array([[ICE, ICE, ICE],
                        [ZERO, ICE, ICE],
                        [ZERO, ICE, ICE]])

        expected = ice.copy()

        actual = _remove_land(ice, cfg)
        npt.assert_array_equal(expected, actual)
