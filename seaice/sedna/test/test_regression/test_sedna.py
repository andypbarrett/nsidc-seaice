from unittest import TestCase
from unittest.mock import patch

import pandas as pd

import seaice.nasateam as nt
import seaice.sedna.sedna as sedna


class Test_update_sea_ice_statistics_daily(TestCase):
    def _build_mock_frame(self):
        df = pd.DataFrame(index=pd.PeriodIndex([], freq='D', name='date'),
                          columns=nt.DAILY_DEFAULT_COLUMNS)
        df = df.set_index([df.index, 'hemisphere'])
        return df

    def _mock_bad_sea_ice_statistics(self, gridset, period, config, failed_qa=False):
        row = {(period, 'N'): {
                                'total_area_km2': 500000,
                                'total_extent_km2': 500000,
                                'missing_km2': 0,
                                'filename': ['foo'],
                                'source_dataset': 'test-dataset',
                                'failed_qa': False}}

        if period == pd.Period('2015-02-02'):
            row[(period, 'N')]['total_extent_km2'] = 0
            return row
        else:
            return row

    def _get_config(self):
        config = {}
        config['hemisphere'] = nt.NORTH
        config['grid_areas'] = config['hemisphere']['grid_areas']
        config['search_paths'] = ['./test_data']
        config['interpolation_radius'] = 0
        config['regression_delta_km2'] = 1
        config['eval_days'] = 2
        config['extent_threshold'] = nt.EXTENT_THRESHOLD
        return config

    @patch('seaice.sedna.sedna._dataframe_from_data_store_daily')
    @patch('seaice.datastore.write_daily_datastore')
    def test_returns_true_on_success(self, mock_write_daily_datastore,
                                     mock__dataframe_from_data_store_daily):
        config = self._get_config()
        mock__dataframe_from_data_store_daily.return_value = self._build_mock_frame()
        dates = pd.period_range('2015-02-04', '2015-02-04')
        result = sedna.update_sea_ice_statistics_daily(dates, config, True)
        self.assertEqual(True, result)
