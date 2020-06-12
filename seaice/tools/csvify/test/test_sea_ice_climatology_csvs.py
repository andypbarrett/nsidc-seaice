import os
import unittest
import shutil

from click.testing import CliRunner
import pandas as pd
from pandas.util.testing import assert_frame_equal

from ..sea_ice_climatology import sea_ice_climatology
from ...fixture_util import create_fixture
import seaice.nasateam as nt
from seaice.nasateam import VERSION_STRING as version


class TestSeaIceClimatologyCSVs(unittest.TestCase):
    this_dir = os.path.dirname(os.path.abspath(__file__))
    test_root = ('../' * 4)
    output_directory = os.path.join(this_dir, test_root, 'test_output')
    fixtures_directory = os.path.join(this_dir, test_root, 'test_data', 'seaice.tools')
    data_store = os.path.join(fixtures_directory, 'clim_daily.p')
    csv_fixture = os.path.join(fixtures_directory, 'clim_daily.csv')

    def rm_out_dir(self):
        try:
            shutil.rmtree(self.output_directory)
        except OSError:
            pass

    def setUp(self):
        self.rm_out_dir()
        os.mkdir(self.output_directory)
        create_fixture(self.csv_fixture, self.data_store, 'D')

    def tearDown(self):
        self.rm_out_dir()
        os.remove(self.data_store)

    def test_create_csvs(self):
        runner = CliRunner()
        runner.invoke(sea_ice_climatology,
                      ['--data_store={}'.format(self.data_store),
                       '--output_directory={}'.format(self.output_directory)])

        for hemi in nt.VALID_HEMISPHERES:
            hemisphere = nt.by_name(hemi)['long_name']
            filename = '{}_seaice_extent_climatology_1981-2010_{}.csv'.format(hemi, version)
            expected = pd.read_csv(os.path.join(self.fixtures_directory, filename), skiprows=1)
            outfile = os.path.join(self.output_directory, hemisphere, 'daily', 'data', filename)
            actual = pd.read_csv(outfile, skiprows=1)
            assert_frame_equal(actual, expected)
