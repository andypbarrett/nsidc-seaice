from osgeo import osr
import unittest

from ..geotiff import _color_to_rgba, _get_cmap, _set_geotransform
from ..geotiff import _set_projection


class Test__color_to_rgba(unittest.TestCase):
    def test_returns_rgba_for_mpl_namedcolor(self):
        """Tests that the correct rbg represenation of a named matplotlib color
        (.e.g, 'black') returns the correct rgb tuple (0, 0, 0)
        """
        actual = _color_to_rgba('black')
        expected = (0, 0, 0, 1)

        self.assertEqual(actual, expected)

    def test_returns_rgba_for_mpl_tuple(self):
        actual = _color_to_rgba((1, 0.5, 0))
        expected = (255, 127, 0, 1)

        self.assertEqual(actual, expected)

    def test_returns_rgba_for_hex(self):
        actual = _color_to_rgba('#31ABFC')
        expected = (49, 171, 252, 1)

        self.assertEqual(actual, expected)


class Test__get_cmap(unittest.TestCase):
    cfg = {'colorbounds': [0, 1, 2, 3.001],
           'colortable': ['#093c70', 'white', '#e9cb00']}

    def test_returns_cmap_dict(self):
        actual = _get_cmap(self.cfg)
        expected = {0: (9, 60, 112, 1),
                    1: (255, 255, 255, 1),
                    2: (233, 203, 0, 1),
                    3: (233, 203, 0, 1)}

        self.assertEqual(actual, expected)


class Test__set_geotransform(unittest.TestCase):

    class Dataset:
        def __init__(self):
            self.actual = None

        def SetGeoTransform(self, x):
            self.actual = x

    def test_sets_correct_geotransform(self):
        dataset = self.Dataset()
        cfg = {'projection': {'pixel_height': 25,
                              'pixel_width': 5,
                              'bounds': [1, 2, 3, 4]}}
        _set_geotransform(cfg, dataset)

        # upper-left-x, pixel-width, row-rotation, upper-left-y,
        # column-rotation, negative-pixel-height
        expected = [1, 5, 0, 4, 0, -25]

        self.assertEqual(dataset.actual, expected)


class Test__set_projection(unittest.TestCase):

    class Dataset:
        def __init__(self):
            self.actual = None

        def SetProjection(self, x):
            self.actual = x

    def test_gets_correct_spatial_ref_from_crs(self):
        dataset = self.Dataset()
        _set_projection('EPSG:3411', dataset)

        # Get the expected value.
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3411)
        expected = srs.ExportToWkt()

        self.assertEqual(dataset.actual, expected)
