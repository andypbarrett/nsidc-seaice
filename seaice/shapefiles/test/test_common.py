import unittest

import seaice.nasateam as nt
from seaice.shapefiles.common import _shapefile_name, _default_archive_paths


class Test__shapefile_name(unittest.TestCase):
    def test_north_monthly_polygon_ver(self):
        config = {
            'polygon': True,
            'polyline': False,
            'median': False,
            'hemi': nt.NORTH,
            'year': 2001,
            'month': 6,
            'version_str': nt.VERSION_STRING,
            'range': (1991, 2010)
        }
        actual = _shapefile_name(config)

        expected = 'extent_N_200106_polygon_{}'.format(nt.VERSION_STRING)

        self.assertEqual(expected, actual)

    def test_south_monthly_polyline_random_version_string(self):
        config = {
            'polygon': False,
            'polyline': True,
            'median': False,
            'hemi': nt.SOUTH,
            'year': 2002,
            'month': 3,
            'version_str': 'alsdkfjasd'
        }
        actual = _shapefile_name(config)

        expected = 'extent_S_200203_polyline_alsdkfjasd'

        self.assertEqual(expected, actual)

    def test_median_dayofyear(self):
        config = {
            'polygon': False,
            'polyline': True,
            'median': True,
            'hemi': nt.NORTH,
            'dayofyear': 350,
            'version_str': nt.VERSION_STRING,
            'range': (1990, 2010)
        }
        actual = _shapefile_name(config)

        expected = 'median_extent_N_350_1990-2010_polyline_{}'.format(nt.VERSION_STRING)

        self.assertEqual(expected, actual)

    def test_median_month_day(self):
        config = {
            'polygon': False,
            'polyline': True,
            'median': True,
            'hemi': nt.SOUTH,
            'month': 12,
            'day': 16,
            'version_str': 'v1',
            'range': (1990, 2010)
        }
        actual = _shapefile_name(config)

        expected = 'median_extent_S_12_16_1990-2010_polyline_v1'

        self.assertEqual(expected, actual)


class Test__default_archive_paths(unittest.TestCase):

    def test_monthly_median_polyline(self):
        config = {
            'month': 7,
            'polygon': False,
            'polyline': True,
            'median': True,
            'range': [1981, 2010],
            'hemi': {'short_name': 'N', 'long_name': 'north'},
        }
        expected = 'north/monthly/shapefiles/shp_median'
        actual = _default_archive_paths(config)
        self.assertEqual(expected, actual)

    def test_daily_median_polyline(self):
        config = {
            'dayofyear': 127,
            'polygon': False,
            'polyline': True,
            'median': True,
            'range': [1981, 2010],
            'hemi': {'short_name': 'N', 'long_name': 'north'},
        }
        expected = 'north/daily/shapefiles/dayofyear_median'
        actual = _default_archive_paths(config)
        self.assertEqual(expected, actual)

    def test_monthly_extent_polygon(self):
        config = {
            'year': 2013,
            'month': 8,
            'polygon': True,
            'polyline': False,
            'median': False,
            'range': [1981, 2010],
            'hemi': {'short_name': 'N', 'long_name': 'north'},
        }
        expected = 'north/monthly/shapefiles/shp_extent/08_Aug'
        actual = _default_archive_paths(config)
        self.assertEqual(expected, actual)

    def test_monthly_extent_polyline(self):
        config = {
            'year': 1980,
            'month': 1,
            'polygon': False,
            'polyline': True,
            'median': False,
            'range': [1981, 2010],
            'hemi': {'short_name': 'S', 'long_name': 'south'},
        }
        expected = 'south/monthly/shapefiles/shp_extent/01_Jan'
        actual = _default_archive_paths(config)
        self.assertEqual(expected, actual)
