import os
import shutil
import unittest

from click.testing import CliRunner

import seaice.nasateam as nt
from ..sea_ice_extent_monthly import sea_ice_extent_monthly
from ..sea_ice_extent_daily import sea_ice_extent_daily
from ...fixture_util import create_fixture


class TestSeaIceExtentCSVs(unittest.TestCase):
    maxDiff = None

    this_dir = os.path.dirname(os.path.abspath(__file__))
    input_directory = os.path.join(this_dir, '..', '..', '..', '..', 'test_data', 'seaice.tools')
    output_directory = os.path.join(this_dir, '..', '..', '..', '..', 'test_output')
    fixtures_directory = os.path.join(this_dir, '..', '..', '..', '..', 'test_data', 'seaice.tools')
    data_store = os.path.join(fixtures_directory, 'daily.p')
    csv_fixture = os.path.join(fixtures_directory, 'daily.csv')
    monthly_data_store = os.path.join(fixtures_directory, 'monthly.p')
    monthly_csv_fixture = os.path.join(fixtures_directory, 'monthly.csv')

    def rm_out_dir(self):
        try:
            shutil.rmtree(self.output_directory)
        except OSError:  # No such file or directory
            pass

    def rm_data_store(self):
        try:
            os.remove(self.data_store)
        except OSError:
            pass

    def rm_monthly_data_store(self):
        try:
            os.remove(self.monthly_data_store)
        except OSError:
            pass

    def setUp(self):
        self.rm_out_dir()
        os.mkdir(self.output_directory)
        create_fixture(self.csv_fixture, self.data_store, 'D')
        create_fixture(self.monthly_csv_fixture, self.monthly_data_store, 'M')

    def tearDown(self):
        self.rm_out_dir()
        self.rm_data_store()
        self.rm_monthly_data_store()

    def test_creates_csvs(self):
        runner = CliRunner()
        runner.invoke(sea_ice_extent_daily, [self.input_directory, self.output_directory])

        for hemisphere in ['north', 'south']:
            out_dir = os.path.join(self.output_directory, hemisphere, 'daily', 'data')
            filename = '{}_seaice_extent_daily_{}.csv'.format(hemisphere[0].capitalize(),
                                                              nt.VERSION_STRING)

            with open(os.path.join(out_dir, filename), 'r') as file_:
                actual_text = file_.read()

            with open(os.path.join(self.fixtures_directory, filename)) as file_:
                expected_text = file_.read()

            self.assertEqual(expected_text, actual_text)

    def test_creates_monthly_csvs(self):
        runner = CliRunner()
        runner.invoke(sea_ice_extent_monthly, [self.input_directory, self.output_directory])

        for hemi in nt.VALID_HEMISPHERES:
            for month in [12]:
                filename = '{hemi}_{month}_extent_{ver}.csv'.format(hemi=hemi, month=month,
                                                                    ver=nt.VERSION_STRING)

                hemisphere = nt.by_name(hemi)['long_name']
                out_dir = os.path.join(self.output_directory, hemisphere, 'monthly', 'data')

                with open(os.path.join(out_dir, filename), 'r') as file_:
                    actual_text = file_.read()

                with open(os.path.join(self.fixtures_directory, filename)) as file_:
                    expected_text = file_.read()

                self.assertEqual(expected_text, actual_text)
