import os
import shutil
from unittest import TestCase

import pandas as pd
from click.testing import CliRunner

from seaice.nasateam import VERSION_STRING as version
from seaice.shapefiles.cli.sii_shp import cli


class Test_cli_sii_shp(TestCase):
    output_dir = 'smoke_test_output'
    runner = CliRunner()

    def removeTestOutput(self):
        try:
            shutil.rmtree(self.output_dir)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()
        os.mkdir(self.output_dir)

    def tearDown(self):
        self.removeTestOutput()

    def test_creates_monthly_polygon_shapefile_zip_with_name_matching_args(self):

        options_str = ('--monthly --polygon -h N -y 2012 '
                       '-m 9 -o {} --flatten').format(self.output_dir)
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(self.output_dir,
                                     'extent_N_201209_polygon_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_monthly_polygon_shapefile_latest(self):

        options_str = '--monthly --polygon -h N --latest 1 -o {} --flatten'.format(self.output_dir)
        options_list = options_str.split(' ')

        date_index = pd.date_range(end=pd.Timestamp.now() - pd.Timedelta('1 day'),
                                   periods=1, freq='M')
        date = date_index[0].date()

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'extent_N_{year}{month:02}_polygon_{version}.zip'.format(year=date.year,
                                                                     month=date.month,
                                                                     version=version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_monthly_polyline_shapefile_zip_with_name_matching_args(self):

        options_str = ('--monthly --polyline -h N -y 2012 -m 9 '
                       '-o {} --flatten').format(self.output_dir)
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(self.output_dir,
                                     'extent_N_201209_polyline_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_monthly_polyline_shapefile_latest(self):

        options_str = '--monthly --polyline -h N --latest 1 -o {} --flatten'.format(self.output_dir)
        options_list = options_str.split(' ')

        date_index = pd.date_range(end=pd.Timestamp.now() - pd.Timedelta('1 day'),
                                   periods=1, freq='M')
        date = date_index[0].date()

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'extent_N_{year}{month:02}_polyline_{version}.zip'.format(year=date.year,
                                                                      month=date.month,
                                                                      version=version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_daily_median_polyline_shapefile_dayofyear(self):

        options_str = ('--daily --median --polyline -h N '
                       '--dayofyear 150 -o {} --flatten').format(self.output_dir)  # noqa
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'median_extent_N_150_1981-2010_polyline_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_daily_median_polyline_shapefile_different_range(self):

        options_str = ('--daily --median --polyline -h S --flatten '
                       '--dayofyear 15 --range 1991,1995 -o {}').format(self.output_dir)  # noqa
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'median_extent_S_015_1991-1995_polyline_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_monthly_median_polyline_shapefile_given_month(self):

        options_str = ('--monthly --median --polyline -h N '
                       '--month 10 -o {} --flatten').format(self.output_dir)  # noqa
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'median_extent_N_10_1981-2010_polyline_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))

    def test_creates_monthly_median_polyline_shapefile_given_range(self):

        options_str = ('--monthly --median --polyline -h S --month 10 '
                       '--range 1991,1995 -o {} --flatten').format(self.output_dir)  # noqa
        options_list = options_str.split(' ')

        self.runner.invoke(cli, options_list, catch_exceptions=False)

        expected_file = os.path.join(
            self.output_dir,
            'median_extent_S_10_1991-1995_polyline_{}.zip'.format(version))

        self.assertTrue(os.path.exists(expected_file))
