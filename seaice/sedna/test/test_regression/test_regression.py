import os
import io
from textwrap import dedent
from unittest import TestCase
from unittest.mock import patch

from click.testing import CliRunner
import numpy.testing as npt
import pandas as pd
from pandas.util.testing import assert_frame_equal

import seaice.data
import seaice.datastore as sds
from seaice.datastore import fixture as fixture
from seaice.sedna.cli.update_sea_ice_statistics_daily import update_sea_ice_statistics_daily
from seaice.sedna.cli.sea_ice_statistics_monthly import sea_ice_statistics_monthly
from seaice.sedna.cli.validate_daily_data import validate_daily_data

TestCase.maxDiff = None

TEST_CONF_DAILY = os.path.join(os.path.dirname(__file__), 'test_conf_daily.yaml')
TEST_CONF_MONTHLY = os.path.join(os.path.dirname(__file__), 'test_conf_monthly.yaml')
TEST_CONF_MONTHLY_WITH_FIXTURE = os.path.join(os.path.dirname(__file__),
                                              'test_conf_monthly_with_fixture.yaml')
TEST_CONF_DAILY_REGIONAL_NORTH = os.path.join(os.path.dirname(__file__),
                                              'test_conf_daily_regional_north.yaml')
TEST_CONF_MONTHLY_REGIONAL_NORTH = os.path.join(os.path.dirname(__file__),
                                                'test_conf_monthly_regional_north.yaml')
TEST_DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                              os.pardir, os.pardir, os.pardir, os.pardir,
                                              'test_data', 'sedna'))


def dataframe_from_text(text, period_index_name):
    text = io.StringIO(text)
    if period_index_name == 'date':
        return fixture.from_daily_csv(text)
    return fixture.from_monthly_csv(text)


def simplify_filename(df_in):
    df = df_in.copy()

    df.filename = df.filename.apply(lambda x: [os.path.basename(f) for f in x])

    return df


class TestValidateData(TestCase):
    output_file = 'test_daily_regional.p'
    conf_file = TEST_CONF_DAILY_REGIONAL_NORTH

    def removeTestOutput(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()

    def tearDown(self):
        self.removeTestOutput()

    def test_data_validation_when_data_already_exists(self):
        text = dedent("""\
        date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,meier2007_hudson_extent_km2,meier2007_hudson_area_km2,meier2007_hudson_missing_km2,failed_qa
        2013-06-01,11604767.336,8906085.423,0.000,N,['nt_20130601_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        2013-06-02,11604767.336,8906085.423,0.000,N,['nt_20130602_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        2013-06-03,11604767.336,8906085.423,0.000,N,['nt_20130603_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        2013-06-04,11604767.336,8906085.423,0.000,N,['nt_20130604_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        2013-06-05,11604767.336,8906085.423,0.000,N,['nt_20130605_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        2013-06-06,20000000.000,8906085.423,0.000,N,['nt_20130606_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
        """)
        df = dataframe_from_text(text, 'date')
        sds.write_daily_datastore(dataframe=df, data_store=self.output_file)

        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        result = runner.invoke(validate_daily_data,
                               ('-h N -s 2013-06-06 -e 2013-06-06 -rd 1 --eval_days 5 '
                                '--write_bad_days True -c ' + self.conf_file).split(' '),
                               catch_exceptions=False)

        assert(result.exit_code == 1)
        text = dedent("""\
            date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,meier2007_hudson_extent_km2,meier2007_hudson_area_km2,meier2007_hudson_missing_km2,failed_qa
            2013-06-01,11604767.336,8906085.423,0.000,N,['nt_20130601_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
            2013-06-02,11604767.336,8906085.423,0.000,N,['nt_20130602_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
            2013-06-03,11604767.336,8906085.423,0.000,N,['nt_20130603_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
            2013-06-04,11604767.336,8906085.423,0.000,N,['nt_20130604_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
            2013-06-05,11604767.336,8906085.423,0.000,N,['nt_20130605_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,False
            2013-06-06,20000000.000,8906085.423,0.000,N,['nt_20130606_f17_v1.1_n.bin'],nsidc-0051,1145394.840,673703.210,0.000,True
            """)
        expected = dataframe_from_text(text, 'date')
        actual = sds.daily_dataframe(self.output_file)
        assert_frame_equal(actual, expected, check_dtype=False)


class TestCLIUpdateSeaIceStatisticsDaily(TestCase):
    output_file = os.path.join(os.path.dirname(__file__), 'test_daily.p')

    def removeTestOutput(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()

    def tearDown(self):
        self.removeTestOutput()

    def test_north_daily(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        runner.invoke(update_sea_ice_statistics_daily,
                      '-h N -s 2015-08-18 -e 2015-08-18 -c {}'.format(TEST_CONF_DAILY).split(' '),
                      catch_exceptions=False)

        df = sds.daily_dataframe(self.output_file)
        row = df.xs((pd.Period('2015-08-18', 'D'), 'N'), level=('date', 'hemisphere'))

        actual_filename = row.filename[0][0]
        expected_filepart = 'nt_20150818_f17_nrt_n.bin'
        self.assertRegex(actual_filename, expected_filepart)

        actual = {
            'area': row.total_area_km2[0],
            'date': row.index[0][0],
            'extent': row.total_extent_km2[0],
            'hemisphere': row.index[0][1],
            'missing': row.missing_km2[0],
            'source_dataset': row.source_dataset[0]
        }

        expected = {
            'area': 3334977.321,
            'date': pd.Period('2015-08-18', 'D'),
            'extent': 5530014.668,
            'hemisphere': 'N',
            'missing': 251753.675,
            'source_dataset': 'nsidc-0081'
        }

        npt.assert_almost_equal(actual.pop('area'),
                                expected.pop('area'))

        npt.assert_almost_equal(actual.pop('extent'),
                                expected.pop('extent'))

        npt.assert_almost_equal(actual.pop('missing'),
                                expected.pop('missing'))

        self.assertDictEqual(actual, expected)

    def test_south_daily(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        runner.invoke(update_sea_ice_statistics_daily,
                      '-h S -s 2015-08-06 -e 2015-08-06 -c {}'.format(TEST_CONF_DAILY).split(' '),
                      catch_exceptions=False)

        df = sds.daily_dataframe(self.output_file)
        row = df.xs((pd.Period('2015-08-06', 'D'), 'S'), level=('date', 'hemisphere'))

        expected_filepart = 'nt_20150806_f17_nrt_s.bin'
        actual_filename = row.filename[0][0]
        self.assertRegex(actual_filename, expected_filepart)

        actual = {
            'area': row.total_area_km2[0],
            'date': row.index[0][0],
            'extent': row.total_extent_km2[0],
            'hemisphere': row.index[0][1],
            'missing': row.missing_km2[0],
            'source_dataset': row.source_dataset[0]
        }

        expected = {
            'area': 9703187.590,
            'date': pd.Period('2015-08-06', 'D'),
            'extent': 12407359.088,
            'hemisphere': 'S',
            'missing': 11880290.578,
            'source_dataset': 'nsidc-0081'
        }

        self.assertDictEqual(actual, expected)

    def test_daily_south_when_data_already_exists(self):
        # setup the test with a few rows of existing data; the data will be
        # modified for the date in which we are interested

        text = """date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,failed_qa
        2014-08-06,34.000,14.000,24.000,S,['nt_20140806_f17_nrt_s.bin'],nsidc-0081,False
        2015-08-06,3.000,1.000,2.000,S,['nt_20150806_f17_nrt_s.bin'],nsidc-0081,False
        2016-08-06,36.000,16.000,26.000,S,['nt_20160806_f17_nrt_s.bin'],nsidc-0081,False
        """
        df = dataframe_from_text(text, 'date')
        sds.write_daily_datastore(dataframe=df, data_store=self.output_file)

        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        runner.invoke(update_sea_ice_statistics_daily,
                      '-h S -s 2015-08-06 -e 2015-08-06 -c {}'.format(TEST_CONF_DAILY).split(' '),
                      catch_exceptions=False)

        actual = sds.daily_dataframe(self.output_file)
        actual = simplify_filename(actual)

        # 2014 and 2016 should be unchanged
        # extent, area, missing should be updated for 2015
        # order of rows and columsn should be unchanged
        text = dedent("""\
        date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,failed_qa
        2014-08-06,34.000,14.000,24.000,S,['nt_20140806_f17_nrt_s.bin'],nsidc-0081,False
        2015-08-06,12407359.088,9703187.590,11880290.578,S,['nt_20150806_f17_nrt_s.bin'],nsidc-0081,False
        2016-08-06,36.000,16.000,26.000,S,['nt_20160806_f17_nrt_s.bin'],nsidc-0081,False
        """)
        expected = dataframe_from_text(text, 'date')
        assert_frame_equal(actual, expected, check_dtype=False)

    def test_daily_with_start_and_end_date(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})

        runner.invoke(update_sea_ice_statistics_daily,
                      '-h S -s 2015-08-06 -e 2015-08-07 -c {}'.format(TEST_CONF_DAILY).split(' '),
                      catch_exceptions=False)

        actual = sds.daily_dataframe(self.output_file)
        actual = simplify_filename(actual)

        text = dedent("""\
        date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,failed_qa
        2015-08-06,12407359.088,9703187.590,11880290.578,S,['nt_20150806_f17_nrt_s.bin'],nsidc-0081,False
        2015-08-07,17531561.018,13747561.298,427899.548,S,['nt_20150807_f17_nrt_s.bin'],nsidc-0081,False
        """)
        expected = dataframe_from_text(text, 'date')
        assert_frame_equal(actual, expected, check_dtype=False)


class TestCLISeaIceStatisticsMonthly(TestCase):
    output_file = os.path.join(os.path.dirname(__file__), 'test_monthly.p')

    def removeTestOutput(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()

    def tearDown(self):
        self.removeTestOutput()

    def test_north_monthly(self):
        def date_parser(date):
            return pd.Period(date, 'M')

        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        runner.invoke(sea_ice_statistics_monthly,
                      '-c {}'.format(TEST_CONF_MONTHLY).split(' '),
                      catch_exceptions=False)

        df = sds.monthly_dataframe(self.output_file)

        # north values
        north_row = df.xs((pd.Period('2013-06', 'M'), 'N'), level=('month', 'hemisphere'))

        north_expected_filepart = '^.*nt_201306[0-9]{2}_f17_v1.1_n.bin$'
        for actual_filename in north_row.filename[0]:
            self.assertRegex(actual_filename, north_expected_filepart)

        north_actual = {
            'area': north_row.total_area_km2[0],
            'month': north_row.index[0][0],
            'extent': north_row.total_extent_km2[0],
            'hemisphere': north_row.index[0][1],
            'missing': north_row.missing_km2[0],
        }
        south_expected = {
            'area': 8953662.1740333345,
            'month': pd.Period('2013-06'),
            'extent': 11360071.404433334,
            'hemisphere': 'N',
            'missing': 0.000
        }
        self.assertDictEqual(north_actual, south_expected)

        # south values
        south_row = df.xs((pd.Period('2013-06', 'M'), 'S'), level=('month', 'hemisphere'))

        south_expected_filepart = '^.*nt_201306[0-9]{2}_f17_v1.1_s.bin$'
        for actual_filename in south_row.filename[0]:
            self.assertRegex(actual_filename, south_expected_filepart)

        south_actual = {
            'area': south_row.total_area_km2[0],
            'month': south_row.index[0][0],
            'extent': south_row.total_extent_km2[0],
            'hemisphere': south_row.index[0][1],
            'missing': south_row.missing_km2[0]
        }
        south_expected = {
            'area': 11266746.304533331,
            'month': pd.Period('2013-06'),
            'extent': 14154831.531999998,
            'hemisphere': 'S',
            'missing': 0.000
        }
        self.assertDictEqual(south_actual, south_expected)

    def test_with_fixture(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        runner.invoke(sea_ice_statistics_monthly, ['-c', TEST_CONF_MONTHLY_WITH_FIXTURE],
                      catch_exceptions=False)

        cols = ['total_extent_km2',
                'total_area_km2',
                'meier2007_eastsiberian_extent_km2',
                'meier2007_eastsiberian_area_km2',
                'meier2007_beaufort_extent_km2',
                'meier2007_beaufort_area_km2',
                'meier2007_okhotsk_extent_km2',
                'meier2007_okhotsk_area_km2',
                'meier2007_chukchi_extent_km2',
                'meier2007_chukchi_area_km2',
                'meier2007_canadianarchipelago_extent_km2',
                'meier2007_canadianarchipelago_area_km2',
                'meier2007_laptev_extent_km2',
                'meier2007_laptev_area_km2',
                'meier2007_barents_extent_km2',
                'meier2007_barents_area_km2',
                'meier2007_greenland_extent_km2',
                'meier2007_greenland_area_km2',
                'meier2007_hudson_extent_km2',
                'meier2007_hudson_area_km2',
                'meier2007_stlawrence_extent_km2',
                'meier2007_stlawrence_area_km2',
                'meier2007_bering_extent_km2',
                'meier2007_bering_area_km2',
                'meier2007_kara_extent_km2',
                'meier2007_kara_area_km2',
                'meier2007_baffin_extent_km2',
                'meier2007_baffin_area_km2',
                'meier2007_centralarctic_extent_km2',
                'meier2007_centralarctic_area_km2',
                'region_s_weddell_extent_km2',
                'region_s_weddell_area_km2',
                'region_s_indian_extent_km2',
                'region_s_indian_area_km2',
                'region_s_pacific_extent_km2',
                'region_s_pacific_area_km2',
                'region_s_ross_extent_km2',
                'region_s_ross_area_km2',
                'region_s_bellingshausen amundsen_extent_km2',
                'region_s_bellingshausen amundsen_area_km2']

        actual = sds.monthly_dataframe(self.output_file)[cols]

        actual = actual.reset_index()
        actual = actual[actual.month <= pd.Period('2020-03', 'M')]
        actual = actual.set_index(['month', 'hemisphere'])

        expected = sds.monthly_dataframe(
            os.path.join(TEST_DATA_DIR, 'daily-prod-2020-04-14-monthly-averages.p')
        )[cols]

        assert_frame_equal(actual, expected)


class TestCLIUpdateSeaIceStatisticsDailyRegionalNorth(TestCase):
    output_file = 'test_daily_regional.p'
    conf_file = TEST_CONF_DAILY_REGIONAL_NORTH

    def removeTestOutput(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()

    def tearDown(self):
        self.removeTestOutput()

    def test_north_daily(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        result = runner.invoke(update_sea_ice_statistics_daily,
                               ['-h', 'N', '-s', '2015-08-18', '-e', '2015-08-18',
                                '-c', self.conf_file],
                               catch_exceptions=False)
        assert(result.exit_code == 0)

        df = sds.daily_dataframe(self.output_file)
        row = df.xs((pd.Period('2015-08-18', 'D'), 'N'), level=('date', 'hemisphere'))

        actual_filename = row.filename[0][0]
        expected_filepart = 'nt_20150818_f17_nrt_n.bin'
        self.assertRegex(actual_filename, expected_filepart)

        actual = {
            'area': row.total_area_km2[0],
            'hemisphere': row.index[0][1],
            'date': row.index[0][0],
            'extent': row.total_extent_km2[0],
            'missing': row.missing_km2[0],
            'hudson_area': row.meier2007_hudson_area_km2[0],
            'hudson_extent': row.meier2007_hudson_extent_km2[0],
            'hudson_missing': row.meier2007_hudson_missing_km2[0],
        }

        expected = {
            'area': 3334977.321,
            'hemisphere': 'N',
            'date': pd.Period('2015-08-18', 'D'),
            'extent': 5530014.668,
            'missing': 251753.675,
            'hudson_area': 33713.454,
            'hudson_extent': 100666.034,
            'hudson_missing': 92220.385
        }

        npt.assert_almost_equal(actual.pop('area'),
                                expected.pop('area'))

        npt.assert_almost_equal(actual.pop('extent'),
                                expected.pop('extent'))

        npt.assert_almost_equal(actual.pop('missing'),
                                expected.pop('missing'))

        npt.assert_almost_equal(actual.pop('hudson_area'),
                                expected.pop('hudson_area'))

        npt.assert_almost_equal(actual.pop('hudson_missing'),
                                expected.pop('hudson_missing'))

        self.assertDictEqual(actual, expected)

    def test_daily_with_start_and_end_date(self):
        runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
        result = runner.invoke(update_sea_ice_statistics_daily,
                               ('-h N -s 2015-02-04 -e 2015-02-06 -c ' + self.conf_file).split(' '),
                               catch_exceptions=False)
        assert(result.exit_code == 0)

        actual = sds.daily_dataframe(self.output_file)
        actual = simplify_filename(actual)

        text = dedent("""\
        date,total_extent_km2,total_area_km2,missing_km2,hemisphere,filename,source_dataset,failed_qa,meier2007_hudson_extent_km2,meier2007_hudson_area_km2,meier2007_hudson_missing_km2
        2015-02-04,14269236.632,12723587.413,0.000,N,['nt_20150204_f17_v1.1_n.bin'],nsidc-0051,False,1231642.667,1193514.663,0.000
        2015-02-05,14232420.723,12656282.842,0.000,N,['nt_20150205_f17_v1.1_n.bin'],nsidc-0051,False,1231642.667,1198230.700,0.000
        2015-02-06,14270219.652,12661128.046,0.000,N,['nt_20150206_f17_v1.1_n.bin'],nsidc-0051,False,1231642.667,1206655.631,0.000
        """)

        expected = dataframe_from_text(text, 'date')
        assert_frame_equal(actual, expected, check_dtype=False)


class TestCLISeaIceStatisticsMonthlyRegionalNorth(TestCase):
    output_file = os.path.join(os.path.dirname(__file__), 'test_monthly_regional.p')
    conf_file = TEST_CONF_MONTHLY_REGIONAL_NORTH

    def removeTestOutput(self):
        try:
            os.remove(self.output_file)
        except FileNotFoundError:
            pass

    def setUp(self):
        self.removeTestOutput()

    def tearDown(self):
        self.removeTestOutput()

    def test_north_monthly(self):
        def date_parser(date):
            return pd.Period(date, 'M')

        with patch.object(seaice.data.getter, 'double_weight_smmr_files', return_value=[None] * 30):
            runner = CliRunner(env={'ROOT_LOG_LEVEL': 'CRITICAL'})
            runner.invoke(sea_ice_statistics_monthly,
                          ('-c ' + self.conf_file).split(' '),
                          catch_exceptions=False)

        df = sds.monthly_dataframe(self.output_file)

        row = df.xs((pd.Period('2013-06', 'M'), 'N'), level=('month', 'hemisphere'))

        expected_filepart = '.*nt_201306[0-9]{2}_f17_v1.1_n.bin$'
        for actual_filename in row.filename[0]:
            self.assertRegex(actual_filename, expected_filepart)

        actual = [row.total_area_km2[0],
                  row.total_extent_km2[0],
                  row.missing_km2[0],
                  row.meier2007_hudson_area_km2[0],
                  row.meier2007_hudson_extent_km2[0],
                  row.meier2007_hudson_missing_km2[0]]

        expected = [8953662.1740333,
                    11360071.4044333,
                    0.,
                    675375.1706667,
                    1021082.3434,
                    0.]
        npt.assert_almost_equal(actual, expected)
        self.assertEqual(row.index[0], (pd.Period('2013-06', 'M'), 'N'))
