import unittest

import numpy.testing as npt
import numpy as np
import rasterio

import seaice.images.util as util


class Test_scale_image(unittest.TestCase):
    def test_rescales_array(self):
        img = np.array([3, 5, 0, 10])
        expected = np.array([-20, 0, -50, 50])
        actual = util.scale_image(img, out_min=-50, out_max=50)
        npt.assert_array_equal(actual, expected)


class Test_mask_bm_image(unittest.TestCase):
    def test_masks_nan(self):
        img = np.array([[1, 1, 1],
                        [2, np.nan, 2],
                        [3, 3, np.nan]])

        # stack the 'img' array to mock a 3d rgb image
        img = np.dstack((img,) * 3)

        expected_mask = np.array([[1, 1, 1],
                                  [1, 0, 1],
                                  [1, 1, 0]])
        expected_img = np.dstack((img, expected_mask))
        actual_img = util.mask_bm_image(img)
        npt.assert_array_equal(actual_img, expected_img)


class Test_apply_gamma(unittest.TestCase):
    def test_returns_same_when_gamma_1(self):
        """Tests that the input numpy array
        is returned when gamma=1
        """
        img = np.array([1.0, 2.0, 3.0])

        actual = util.apply_gamma(img, out_min=1, out_max=3, gamma=1)
        npt.assert_array_equal(actual, img)

    def test_returns_custom_range(self):
        """Test that the output scales between out_min and out_max"""
        img = np.arange(5)

        actual = util.apply_gamma(img, out_min=0, out_max=255, gamma=1)
        self.assertEqual(actual.min(), 0)
        self.assertEqual(actual.max(), 255)

    def test_returns_expected_values(self):
        """Provide some assurance that the code hasn't changed
        in an unexpected way by checking that the output values
        match what is currently expected.
        """
        img = np.array([0, 12, 22, 83, 100, 143])

        expected = np.array([0, 31.03191719, 51.94740138,
                             160.59089818, 188.150142,
                             255])
        actual = util.apply_gamma(img, out_min=0, out_max=255,
                                  gamma=0.85)
        npt.assert_almost_equal(actual, expected, decimal=5)


class Test__compute_bounds(unittest.TestCase):
    """Tests that the correct bounds list is returned from
    util._compute_bounds
    """
    def setUp(self):
        self.width = 10
        self.height = 20
        self.left = -180
        self.top = 90
        self.pixel_width = 1
        self.pixel_height = 2

        self.expected = [self.left,
                         self.left + self.pixel_width * self.width,
                         self.top + -self.pixel_height * self.height,
                         self.top]

    def test_returns_bounds_from_transform(self):
        transform = rasterio.Affine(self.pixel_width,
                                    0,
                                    self.left,
                                    0,
                                    -self.pixel_height,
                                    self.top)

        actual = util._compute_new_bounds(self.width, self.height, transform=transform)
        self.assertEquals(self.expected, actual)

    def test_returns_bounds_from_other_args(self):
        actual = util._compute_new_bounds(self.width, self.height,
                                          pixel_width=self.pixel_width,
                                          pixel_height=self.pixel_height,
                                          left=self.left, top=self.top)
        self.assertEquals(self.expected, actual)

    def test_returns_bounds_without_pixel_height(self):
        actual = util._compute_new_bounds(self.width, self.height,
                                          pixel_width=self.pixel_width,
                                          left=self.left, top=self.top)

        self.expected[2] = self.top + -self.pixel_width * self.height
        self.assertEquals(self.expected, actual)
