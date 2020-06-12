import datetime as dt
import unittest
from unittest.mock import patch

import seaice.nasateam as nt
import numpy as np
import numpy.testing as npt

import seaice.images.api as api


class Test__get_ice_data(unittest.TestCase):
    gridset = {'data': [], 'metadata': {}}

    # helper function to deal with _get_ice_data args that are passed to
    # seaicedata, so that the tests can focus on the args that determine the
    # seaicedata function to call
    def get_ice_data(self, temporality, data_type, blue_marble=False, trend_start_year=None):
        cfg = {'projection': {'pixel_width': 25000, 'pixel_height': 25000}}
        return api._get_ice_data(**{'nt_hemi': {'short_name': 'N'},
                                    'date': dt.date(2014, 10, 24),
                                    'temporality': temporality,
                                    'allow_bad_data': False,
                                    'data_type': data_type,
                                    'year_range': (1981, 2010),
                                    'blue_marble': blue_marble,
                                    'cfg_in': cfg,
                                    'trend_start_year': trend_start_year})

    @patch('seaice.data.concentration_monthly_anomaly')
    def test_seaicedata_concentration_monthly_anomaly(self, mock_concentration_monthly_anomaly):
        mock_concentration_monthly_anomaly.return_value = self.gridset

        self.get_ice_data('monthly', 'anomaly')

        mock_concentration_monthly_anomaly.assert_called_with(allow_empty_gridset=False,
                                                              hemisphere={'short_name': 'N'},
                                                              month=10,
                                                              start_year=1981,
                                                              end_year=2010,
                                                              year=2014)

    @patch('seaice.data.concentration_daily')
    def test_seaicedata_concentration_daily(self, mock_concentration_daily):
        mock_concentration_daily.return_value = self.gridset

        self.get_ice_data('daily', 'concentration')

        mock_concentration_daily.assert_called_with({'short_name': 'N'},
                                                    2014, 10, 24,
                                                    allow_bad_dates=False,
                                                    allow_empty_gridset=False,
                                                    drop_invalid_ice=True)

    @patch('seaice.data.concentration_monthly')
    def test_seaicedata_concentration_monthly(self, mock_concentration_monthly):
        mock_concentration_monthly.return_value = self.gridset

        self.get_ice_data('monthly', 'concentration')

        mock_concentration_monthly.assert_called_with({'short_name': 'N'},
                                                      2014, 10,
                                                      allow_empty_gridset=False,
                                                      drop_invalid_ice=True)

    @patch('seaice.data.extent_daily')
    def test_seaicedata_extent_daily(self, mock_extent_daily):
        mock_extent_daily.return_value = self.gridset

        self.get_ice_data('daily', 'extent')

        mock_extent_daily.assert_called_with({'short_name': 'N'},
                                             year=2014, month=10, day=24,
                                             allow_empty_gridset=False)

    @patch('seaice.data.extent_monthly')
    def test_seaicedata_extent_monthly(self, mock_extent_monthly):
        mock_extent_monthly.return_value = self.gridset

        self.get_ice_data('monthly', 'extent')

        mock_extent_monthly.assert_called_with({'short_name': 'N'},
                                               year=2014, month=10,
                                               allow_empty_gridset=False)

    @patch('seaice.data.concentration_monthly')
    def test_masks_blue_marble_extent_ice(self, mock_concentration_monthly):
        self.gridset['data'] = np.array([[0, 0.3, 15],
                                         [15, 0, 251],
                                         [255, 253, 254],
                                         [255, 0, 15]])

        mock_concentration_monthly.return_value = self.gridset

        expected_mask = np.array([[True,  True,  True,  True,  True, False],
                                  [True,  True,  True,  True, False, False],
                                  [True,  True,  True, False, False, False],
                                  [True,  True,  True,  True, False, False],
                                  [False, False,  True,  True, False, False],
                                  [False, False,  True,  True,  True,  True],
                                  [False, False,  True,  True,  True,  True],
                                  [False, False,  True,  True,  True, False]], dtype=bool)

        actual, _ = self.get_ice_data('monthly', 'extent', blue_marble=True)

        npt.assert_array_equal(expected_mask, actual['data'].mask)

    @patch('seaice.data.concentration_monthly')
    def test_masks_blue_marble_conc_ice(self, mock_conc_monthly):
        self.gridset['data'] = np.array([[0, 0.3, 1],
                                         [15, 20, 251],
                                         [255, 253, 254],
                                         [255, 15, 100]])

        expected_mask = [[True, True, True],
                         [False, False, False],
                         [False, True, True],
                         [False, False, False]]

        mock_conc_monthly.return_value = self.gridset

        actual, _ = self.get_ice_data('monthly', 'concentration', blue_marble=True)

        npt.assert_array_equal(expected_mask, actual['data'].mask)

    @patch('seaice.data.concentration_monthly_trend')
    def test_seaicedata_concentration_monthly_trend(self, mock_concentration_monthly_trend):
        mock_concentration_monthly_trend.return_value = self.gridset

        self.get_ice_data('monthly', 'trend')

        mock_concentration_monthly_trend.assert_called_with(hemisphere={'short_name': 'N'},
                                                            month=10,
                                                            year=2014,
                                                            trend_start_year=None,
                                                            clipping_threshold=None)

    @patch('seaice.data.concentration_monthly_trend')
    def test_sid_concentration_monthly_trend_start_year(self, mock_concentration_monthly_trend):
        mock_concentration_monthly_trend.return_value = self.gridset

        self.get_ice_data('monthly', 'trend', trend_start_year=2010)

        mock_concentration_monthly_trend.assert_called_with(hemisphere={'short_name': 'N'},
                                                            month=10,
                                                            year=2014,
                                                            trend_start_year=2010,
                                                            clipping_threshold=None)


class Test__land_coast_grid(unittest.TestCase):

    def setUp(self):
        self.expected_grid = np.array([0, 0, 253, 254, 0, 0, 0, 0])
        self.loci_mask_return = np.ma.array([nt.Loci.ocean.value,
                                             nt.Loci.valid_ice.value,
                                             nt.Loci.coast.value,
                                             nt.Loci.land.value,
                                             nt.Loci.lake.value,
                                             nt.Loci.shore.value,
                                             nt.Loci.near_shore.value,
                                             nt.Loci.off_shore.value])

    @patch('seaice.images.api.nt.loci_mask')
    def test_converts_loci_return_values_properly(self, loci_mask_mock):
        loci_mask_mock.return_value = self.loci_mask_return

        actual = api._land_coast_grid(nt.NORTH, dt.date.today())

        npt.assert_array_equal(self.expected_grid, actual)


@patch('seaice.images.api._land_coast_grid')
class Test__land_coast_gridset(unittest.TestCase):

    def setUp(self):
        self.mocked_grid = np.array([nt.Loci.ocean.value,
                                     nt.Loci.ocean.value,
                                     nt.FLAGS['coast'],
                                     nt.FLAGS['land'],
                                     nt.Loci.ocean.value,
                                     nt.Loci.ocean.value,
                                     nt.Loci.ocean.value,
                                     nt.Loci.ocean.value])

    def test_converts_loci_return_values_properly(self, land_coast_grid_mock):
        land_coast_grid_mock.return_value = self.mocked_grid
        expected = self.mocked_grid

        actual_gridset = api._land_coast_gridset(nt.NORTH, dt.date.today())

        npt.assert_array_equal(expected, actual_gridset['data'])

    def test_converts_adds_correct_metadata(self, land_coast_grid_mock):
        land_coast_grid_mock.return_value = None

        expected_metadata = {'files': [''],
                             'missing_value': 255.}

        actual = api._land_coast_gridset(nt.NORTH, dt.date.today())

        self.assertEqual(expected_metadata, actual['metadata'])


class Test__source_filename(unittest.TestCase):
    def test_with_files(self):
        metadata = {'files': ['file1.bin', 'file2.bin']}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, 'file1.bin')

    def test_empty_file_list(self):
        metadata = {'files': []}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, '')

    def test_no_file_list(self):
        metadata = {}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, '')

    def test_monthly_anomaly_with_files(self):
        metadata = {'type': 'Monthly Anomaly',
                    'month_files': ['file1.bin', 'file2.bin']}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, 'file1.bin')

    def test_monthly_anomaly_empty_file_list(self):
        metadata = {'type': 'Monthly Anomaly',
                    'month_files': []}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, '')

    def test_monthly_anomaly_no_file_list(self):
        metadata = {'type': 'Monthly Anomaly'}
        actual = api._source_filename(metadata)
        self.assertEqual(actual, '')


class Test__prepare_extent_no_land(unittest.TestCase):

    def setUp(self):
        self.grid = np.array([[50, 50, 0],
                              [100, 251, 100],
                              [0, 0, 0]])

        #  Results of bilinear resampling the above grid with 251 replaced by 100.
        self.bilinear_grid = np.array([[50, 50, 50, 40, 20,  0],
                                       [70, 70, 70, 64, 52, 40],
                                       [90, 90, 90, 88, 84, 80],
                                       [80, 80, 80, 80, 80, 80],
                                       [40, 40, 40, 40, 40, 40],
                                       [0,   0,  0,  0,  0,  0]])

        self.grid_missing = np.array([[50, 50, 0],
                                      [100, 251, 255],
                                      [0, 0, 0]])

        # Results of bilinear resampling the grid_missing, with 255 replaced
        # with 0 and 251 replaced with 100.
        self.bilinear_missing = np.array([[50, 50, 50, 40, 20,  0],
                                          [70, 70, 70, 56, 28,  0],
                                          [90, 90, 90, 72, 36,  0],
                                          [80, 80, 80, 64, 32,  0],
                                          [40, 40, 40, 32, 16,  0],
                                          [0,   0,  0,  0,  0,  0]])

        self.gridset = {'data': None, 'metadata': {}}

    def test_prepare_no_missing(self):
        self.gridset['data'] = self.grid
        expected_mask = (self.bilinear_grid < 15).astype(bool)
        actual = api._prepare_extent_no_land(self.gridset, scale_factor=2)
        npt.assert_array_equal(expected_mask, actual['data'].mask)

    def test_prepare_with_missing(self):
        self.gridset['data'] = self.grid_missing
        expected_mask = (self.bilinear_missing < 15).astype(bool)
        expected_mask[2:4, 4:] = False
        actual = api._prepare_extent_no_land(self.gridset, scale_factor=2)
        self.assertTrue(np.all(actual['data'].data[2:4, 4:] == 255))
        npt.assert_array_equal(expected_mask, actual['data'].mask)


class Test__sensor_string(unittest.TestCase):
    def _gridset(self, files):
        return {'metadata': {'files': files}}

    def test_returns_single_sensor(self):
        gridset1 = self._gridset(['nt_20010106_f13_v1.1_n.bin'])
        gridset2 = self._gridset(['nt_20010107_f13_v1.1_n.bin'])
        actual = api._sensor_string(gridset1, gridset2)
        expected = 'f13'
        self.assertEqual(actual, expected)

    def test_returns_multiple_sensors_oldest_sensor_first(self):
        gridset1 = self._gridset(['nt_20010106_n07_v1.1_n.bin'])
        gridset2 = self._gridset(['nt_20010107_f08_v1.1_n.bin'])
        actual = api._sensor_string(gridset1, gridset2)
        expected = 'n07-f08'
        self.assertEqual(actual, expected)
