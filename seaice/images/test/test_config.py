# Test configuration items.
import datetime as dt
import copy
import unittest
from unittest.mock import patch

import numpy.testing as npt
import numpy as np
import pandas as pd

import seaice.images.config as config
from seaice.images.errors import SeaIceImagesBadConfiguration
from seaice.images.errors import SeaIceImagesNotImplementedError


class Test__rescale_fontsize(unittest.TestCase):

    def test_simple_scale(self):
        start_dict = {'fontsize': 5.}
        expected = {'fontsize': 10.}
        actual = config._rescale_fontsize(start_dict, 2.)
        self.assertEqual(actual, expected)

    def test_only_replaces_fontsized_things(self):
        start_dict = {'this_is_fontsize': 5.,
                      'This is not': 5.}
        expected = {'this_is_fontsize': 10.,
                    'This is not': 5.}
        actual = config._rescale_fontsize(start_dict, 2.)
        self.assertEqual(actual, expected)

    def test_replaces_deeply(self):
        start_dict = {'fontsize': 5.,
                      'b': 5.,
                      'c': {'deep_fontsize': 3., 'd': 'something'}}

        expected = {'fontsize': 10.,
                    'b': 5.,
                    'c': {'deep_fontsize': 6., 'd': 'something'}}
        actual = config._rescale_fontsize(start_dict, 2.)
        self.assertEqual(actual, expected)

    def test_dont_double_recurse_or_multiply_a_dict_by_a_number(self):
        start_dict = {'a': {'fontsizes': {'title_fontsize': 3.}}}
        expected = {'a': {'fontsizes': {'title_fontsize': 6.}}}
        actual = config._rescale_fontsize(start_dict, 2.)
        self.assertEqual(expected, actual)


class test__merge_keys(unittest.TestCase):

    def test__merge_keys_merges(self):
        parent_dict = {'source_attribution': {
            'text': 'my text',
            'kwargs': {'k1': 'right', 'k2': 8.0}
        }}

        child_dict = {'source_attribution': {
            'position': 'my position'
        }}
        expected = {'source_attribution': {
            'text': 'my text',
            'kwargs': {'k1': 'right', 'k2': 8.0},
            'position': 'my position'
        }}
        actual = config._merge_keys(parent_dict, child_dict)
        self.assertEqual(expected, actual)

    def test__merge_keys_appends(self):
        parent_dict = {'source_attribution': {
            'text': 'my text',
            'kwargs': {'k1': 'right', 'k2': 8.0}
        }}

        child_dict = {'otherkey': 'othervalue'}
        expected = {'source_attribution':
                    {
                        'text': 'my text',
                        'kwargs': {'k1': 'right', 'k2': 8.0}
                    },
                    'otherkey': 'othervalue'}
        actual = config._merge_keys(parent_dict, child_dict)
        self.assertEqual(expected, actual)

    def test__merge_keys_raises_problem_try_to_replace_existing(self):
        parent_dict = {'alpha': {'beta': 'my beta'}}
        child_dict = {'alpha': 'othervalue'}
        with self.assertRaises(SeaIceImagesBadConfiguration) as cm:
            config._merge_keys(parent_dict, child_dict)
        self.assertRegex(str(cm.exception), 'alpha')

    def test__merge_keys_opposite_raises_problem_try_to_replace_existing(self):
        parent_dict = {'alpha': 'othervalue'}
        child_dict = {'alpha': {'beta': 'my beta'}}
        with self.assertRaises(SeaIceImagesBadConfiguration):
            config._merge_keys(parent_dict, child_dict)

    def test__merge_keys_updates_existing_dictionary(self):
        parent_dict = {'first': {'all_rows': {'pass': 'dog', 'number': '1'}}}
        child_dict = {'first': {'all_rows': {'fail': 'cat', 'number': '5'}}}
        expected = {'first': {'all_rows': {'pass': 'dog', 'fail': 'cat', 'number': '5'}}}
        actual = config._merge_keys(parent_dict, child_dict)
        self.assertEqual(expected, actual)


class Test__prune_keys(unittest.TestCase):

    def test__prune_keys_prunes_single_key(self):
        cfg = {'alpha': 'value', 'beta': {'alpha': 'value2'}}
        expected = {'beta': {'alpha': 'value2'}}
        actual = config._prune_keys(cfg, 'alpha')
        self.assertEqual(expected, actual)

    def test__prune_keys_prunes_many_keys(self):
        cfg = {'alpha': 'value',
               'beta': {'alpha': 'value2'},
               'zeta': {'beta': 'stillhere'}}
        expected = {'zeta': {'beta': 'stillhere'}}
        actual = config._prune_keys(cfg, 'alpha', 'beta')
        self.assertEqual(expected, actual)


class Test__substitute_colortable(unittest.TestCase):

    def test__substitute_colortable_does_nothing_with_nothing_to_interpret(self):
        cfg = {'colortable': ['#9eeea1', '#9e239c', 'red'],
               'namedcolors': {}}
        expected = copy.deepcopy(cfg)
        actual = config._substitute_colortable(cfg)
        self.assertEqual(expected, actual)

    def test__substitute_colortable_substitutes_correctly_formatted_values(self):
        cfg = {'colortable': ['#9eeea1', '#9e239c', '{stupidstuff}'],
               'namedcolors': {'stupidstuff': 'goofy-colorname'}}
        expected = copy.deepcopy(cfg)
        expected['colortable'][2] = 'goofy-colorname'
        actual = config._substitute_colortable(cfg)
        self.assertEqual(expected, actual)

    def test__substitute_colortable_ignores_namedcolors_keys(self):
        cfg = {'colortable': ['#9eeea1', '#9e239c', '{stupidstuff}'],
               'namedcolors': {'stupidstuff': 'goofy-colorname',
                               'nothing-to-interpolate-here': '#FFFFFF'}}
        expected = copy.deepcopy(cfg)
        expected['colortable'][2] = 'goofy-colorname'
        actual = config._substitute_colortable(cfg)
        self.assertEqual(expected, actual)

    def test__substitute_colortable_errors_if_interpolate_has_no_match(self):
        cfg = {'colortable': ['#9eeea1', '#9e239c', '{stupidstuff}'],
               'namedcolors': {'nothing-to-interpolate-here': '#FFFFFF'}}

        with self.assertRaises(SeaIceImagesBadConfiguration):
            config._substitute_colortable(cfg)


class Test__substitute_colors(unittest.TestCase):
    def test_substitutes(self):
        color_list = ['{ocean}', '{land}', '#137AE3', '{missing}', '#1684EB']

        named_colors = {'lake': '#133399', 'land': '#777777',
                        'missing': '#e9cb00', 'ocean': '#093c70'}

        actual = config._substitute_colors(color_list, named_colors)

        expected = ['#093c70', '#777777', '#137AE3', '#e9cb00', '#1684EB']

        self.assertEqual(actual, expected)

    def test_substitutes_with_tuples(self):
        color_list = ['{ocean}', '{land}', '#137AE3', '{missing}', '#1684EB']

        named_colors = {'lake': '#133399', 'land': '#777777',
                        'missing': '#e9cb00', 'ocean': (0.0, 0.0, 0.0, 0.0)}

        actual = config._substitute_colors(color_list, named_colors)

        expected = [(0.0, 0.0, 0.0, 0.0), '#777777', '#137AE3', '#e9cb00', '#1684EB']

        self.assertEqual(actual, expected)


class Test__format_label(unittest.TestCase):

    def test_formats_title_when_substitution_available(self):
        in_str = 'Sea Ice Concentration, {date}'
        date_format = '%d %b %Y'
        date = dt.date(2112, 3, 14)
        actual = config._format_label(in_str, {}, date, date_format)
        expected = 'Sea Ice Concentration, 14 Mar 2112'
        self.assertEqual(expected, actual)

    def test_formats_title_for_monthly_when_format_provided(self):
        in_str = 'Sea Ice Concentration, {date}'
        date_format = '%b %Y'
        date = dt.date(2112, 3, 14)
        actual = config._format_label(in_str, {}, date, date_format)
        expected = 'Sea Ice Concentration, Mar 2112'
        self.assertEqual(expected, actual)

    def test_works_with_no_substitution(self):
        in_str = 'Sea Ice Concentration'
        date = dt.date(2112, 3, 14)
        actual = config._format_label(in_str, {}, date, None)
        expected = 'Sea Ice Concentration'
        self.assertEqual(expected, actual)


class Test_set_source_attribute(unittest.TestCase):

    def setUp(self):
        self.cfg = {'source_attribution': {'text': None},
                    'image_labels': ['source_attribution']}

    def test_sets_near_real_time(self):
        cfg = self.cfg
        filename = ('/projects/DATASETS/nsidc0081_nrt_nasateam_seaice/'
                    'north/nt_20150101_f17_nrt_n.bin')
        expected = {'source_attribution': {'text': 'near-real-time data'},
                    'image_labels': ['source_attribution']}
        actual = config.set_source_attribute(cfg, filename)
        self.assertEqual(expected, actual)

    def test_sets_final(self):
        cfg = {'source_attribution': {}}
        filename = ('/projects/DATASETS/nsidc0051_gsfc_nasateam_seaice'
                    '/final-gsfc/north/daily/1983/nt_19830101_n07_v1.1_n.bin')
        expected = {'source_attribution': {'text': 'final data'}}
        actual = config.set_source_attribute(cfg, filename)
        self.assertEqual(expected, actual)

    def test_removes_source_attribute_if_bad_filename(self):
        cfg = self.cfg
        filename = '/1983/nt_undetermined_filename_bin'
        expected = {'source_attribution': {'text': None},
                    'image_labels': []}
        actual = config.set_source_attribute(cfg, filename)
        self.assertEqual(expected, actual)


class Test_rescale_config(unittest.TestCase):

    def test_scales_correctly(self):
        cfg = {'title': {'kwargs': {'color': 'white', 'fontsize': 16.0},
                         'position': [0.038, 0.953],
                         'text': 'Sea Ice Concentration, 30 Jan 2015'},
               'canvas': {'scale': 2.,
                          'pixel_dims': [1, 20]}}

        expected = {'title': {'kwargs': {'color': 'white', 'fontsize': 32.0},
                              'position': [0.038, 0.953],
                              'text': 'Sea Ice Concentration, 30 Jan 2015'},
                    'canvas': {'scale': 2.,
                               'pixel_dims': [2, 40]}}
        actual = config._rescale_config(cfg)

        npt.assert_equal(expected, actual)


class Test_set_sub_title(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            'sub-title': {'text': 'Total Area = {value} million sq km'},
            'image_labels': [],
            'hemisphere': 'N'
        }

    @patch('seaice.images.config._monthly_data_millions_km2')
    def test_formats_title_and_updates_image_labels_when_area_provided(self, data_mock):
        cfg = self.cfg
        data_mock.return_value = '1.3'
        expected = {'sub-title': {'text': 'Total Area = 1.3 million sq km'},
                    'image_labels': ['sub-title'],
                    'hemisphere': 'N'}
        actual = config.set_sub_title(cfg, dt.date(2010, 1, 1),
                                      'concentration', 'monthly', None)
        self.assertEqual(expected, actual)

    @patch('seaice.images.config._monthly_data_millions_km2')
    def test_returns_unchanged_if_data_is_None(self, data_mock):
        cfg = self.cfg
        data_mock.return_value = None
        expected = copy.deepcopy(cfg)
        actual = config.set_sub_title(cfg, dt.date(2010, 1, 1),
                                      'concentration', 'monthly', None)
        self.assertEqual(expected, actual)

    @patch('seaice.images.config._monthly_data_millions_km2')
    def test_returns_unchanged_if_data_is_an_emptystring(self, data_mock):
        cfg = self.cfg
        data_mock.return_value = ''
        expected = copy.deepcopy(cfg)
        actual = config.set_sub_title(cfg, dt.date(2010, 1, 1),
                                      'concentration', 'monthly', None)
        self.assertEqual(expected, actual)

    def test_returns_unchanged_if_image_type_is_trend(self):
        cfg = self.cfg
        expected = copy.deepcopy(cfg)
        actual = config.set_sub_title(cfg, dt.date(2010, 1, 1),
                                      'trend', 'monthly', None)
        self.assertEqual(expected, actual)


class Test_set_output(unittest.TestCase):

    @patch('os.getcwd')
    def test_returns_custom_output_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_version': 'ver', 'hemisphere': 'S'}
        expected = 'test_filename.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   expected,
                                   'extent',
                                   'daily',
                                   flatten=True)

        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_custom_output_filename_when_hires_provided(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_version': 'ver', 'hires': True, 'hemisphere': 'S'}
        expected = 'test_filename.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   expected,
                                   'extent',
                                   'daily',
                                   flatten=True)

        self.assertEqual(expected, actual['output'])

    @patch('os.path.isdir')
    @patch('os.getcwd')
    def test_returns_default_filename_in_custom_output_existing_dir(self, mock_cwd, mock_isdir):
        mock_cwd.return_value = ''
        mock_isdir.return_value = True
        cfg = {'output_postfix': 'ext', 'output_version': 'ver', 'hemisphere': 'S'}
        output = 'definitely_a_real_dir'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   output,
                                   'extent',
                                   'daily',
                                   flatten=True)

        expected = 'definitely_a_real_dir/S_20120102_ext_ver.png'

        self.assertEqual(expected, actual['output'])

    @patch('os.path.isdir')
    @patch('os.getcwd')
    def test_returns_hires_filename_in_custom_output_existing_dir(self, mock_cwd, mock_isdir):
        mock_cwd.return_value = ''
        mock_isdir.return_value = True
        cfg = {'output_postfix': 'ext', 'output_version': 'ver', 'hires': True,
               'hemisphere': 'S'}
        output = 'definitely_a_real_dir'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   output,
                                   'extent',
                                   'daily',
                                   flatten=True)

        expected = 'definitely_a_real_dir/S_20120102_ext_hires_ver.png'

        self.assertEqual(expected, actual['output'])

    @patch('os.path.isdir')
    @patch('os.getcwd')
    def test_returns_full_archive_directory_structure(self, mock_cwd, mock_isdir):
        mock_cwd.return_value = ''
        mock_isdir.return_value = True
        cfg = {'output_postfix': 'ext', 'output_version': 'ver', 'hemisphere': 'S'}
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'daily',
                                   flatten=False)

        expected = 'south/daily/images/2012/01_Jan/S_20120102_ext_ver.png'

        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_daily_extent_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'ext', 'output_version': 'ver', 'hemisphere': 'S'}
        expected = 'S_20120102_ext_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'daily',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_hires_daily_extent_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'ext', 'output_version': 'ver', 'hires': True,
               'hemisphere': 'S'}
        expected = 'S_20120102_ext_hires_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'daily',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_daily_concentration_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'conc', 'output_version': 'ver', 'hemisphere': 'S'}
        expected = 'S_20120102_conc_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'concentration',
                                   'daily',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_monthly_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'conc', 'output_version': 'ver',
               'hemisphere': 'N'}
        expected = 'N_201201_conc_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'concentration',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_hires_monthly_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'conc', 'output_version': 'ver', 'hires': True,
               'hemisphere': 'N'}
        expected = 'N_201201_conc_hires_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'concentration',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_geotiff_ext_when_true(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'conc', 'output_version': 'ver', 'hires': True,
               'hemisphere': 'N'}
        expected = 'N_201201_conc_hires_ver.tif'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'concentration',
                                   'monthly',
                                   flatten=True,
                                   geotiff=True)
        self.assertEqual(expected, actual['output'])

    @patch('seaice.images.config._ensure_path_exists')
    @patch('os.path.isdir')
    def test_returns_custom_output_dir_with_file(self, mock_isdir, mock_ensure_path_exists):
        cfg = {'hemisphere': 'N'}
        expected = '/a/test/dir/test_filename.png'
        mock_isdir.return_value = False

        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   expected,
                                   'concentration',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.path.isdir')
    def test_returns_custom_output_dir_with_no_file(self, mock_isdir):
        cfg = {'output_postfix': 'conc', 'output_version': 'ver', 'hemisphere': 'N'}
        expected = '/a/test/dir/N_201201_conc_ver.png'
        mock_isdir.return_value = True

        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   '/a/test/dir',
                                   'concentration',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.path.isdir')
    def test_returns_custom_output_dir_with_no_file_with_slash(self, mock_isdir):
        cfg = {'output_postfix': 'conc', 'output_version': 'ver', 'hemisphere': 'N'}
        expected = '/a/test/dir/N_201201_conc_ver.png'
        mock_isdir.return_value = True

        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   '/a/test/dir/',
                                   'concentration',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_blue_marble_monthly_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'extn', 'output_version': 'ver',
               'blue_marble_image': {'bm_dir': ''}, 'hemisphere': 'N'}
        expected = 'N_201201_extn_blmrbl_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'monthly',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_blue_marble_daily_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'extn', 'output_version': 'ver',
               'blue_marble_image': {'bm_dir': ''}, 'hemisphere': 'S'}
        expected = 'S_20120102_extn_blmrbl_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'daily',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_returns_default_hires_blue_marble_daily_filename(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'extn', 'output_version': 'ver',
               'blue_marble_image': {'bm_dir': ''}, 'hires': True,
               'hemisphere': 'S'}
        expected = 'S_20120102_extn_blmrbl_hires_ver.png'
        actual = config.set_output(cfg,
                                   dt.date(2012, 1, 2),
                                   None,
                                   'extent',
                                   'daily',
                                   flatten=True)
        self.assertEqual(expected, actual['output'])

    @patch('os.getcwd')
    def test_trend_images_dont_include_year_and_say_trend(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {'output_postfix': 'trend', 'output_version': 'ver', 'hemisphere': 'N'}

        expected = 'N_01_trend_ver.png'

        actual = config.set_output(cfg,
                                   date=dt.date(2012, 1, 1),
                                   output=None,
                                   image_type='trend',
                                   temporality='monthly',
                                   flatten=True)

        self.assertEqual(expected, actual['output'])


class Test_set_sos_output(unittest.TestCase):
    @patch('os.getcwd')
    def test_sets_output_filename_with_dates_and_sensor(self, mock_cwd):
        mock_cwd.return_value = ''
        cfg = {}
        date_range = pd.date_range(start='2000-01-01', end='2000-01-07', freq='D')

        actual = config.set_sos_output(cfg, date_range, output='', sensor='anySensor')
        expected = 'nt_monthext_20000101-20000107_anySensor_sos.png'

        self.assertEqual(expected, actual['output'])


class Test__tree_structure(unittest.TestCase):
    def test_with_flatten_returns_blank_daily(self):
        hemi = 'N'
        temporality = 'daily'
        date = dt.date(2012, 9, 17)
        flatten = True
        geotiff = False

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = '.'
        self.assertEqual(actual, expected)

    def test_daily_september_north_image(self):
        hemi = 'N'
        temporality = 'daily'
        date = dt.date(2012, 9, 17)
        flatten = False
        geotiff = False

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = 'north/daily/images/2012/09_Sep'
        self.assertEqual(actual, expected)

    def test_monthly_december_south_image(self):
        hemi = 'S'
        temporality = 'monthly'
        date = dt.date(2012, 12, 17)
        flatten = False
        geotiff = False

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = 'south/monthly/images/12_Dec'
        self.assertEqual(actual, expected)

    def test_with_flatten_returns_blank_monthly(self):
        hemi = 'S'
        temporality = 'monthly'
        date = dt.date(2012, 12, 17)
        flatten = True
        geotiff = False

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = '.'
        self.assertEqual(actual, expected)

    def test_monthly_january_south_geotiff(self):
        hemi = 'S'
        temporality = 'monthly'
        date = dt.date(2012, 1, 17)
        flatten = False
        geotiff = True

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = 'south/monthly/geotiff/01_Jan'
        self.assertEqual(actual, expected)

    def test_daily_june_north_geotiff(self):
        hemi = 'N'
        temporality = 'daily'
        date = dt.date(1991, 6, 15)
        flatten = False
        geotiff = True

        actual = config._tree_structure(hemi, temporality, date, flatten,
                                        geotiff)

        expected = 'north/daily/geotiff/1991/06_Jun'
        self.assertEqual(actual, expected)


class Test__monthly_data_millions_km2(unittest.TestCase):

    def _sample_frame(self):
        frame = pd.DataFrame([[8131362.0, 5238356.0, 0.0, 'N', ['files'], 'nsidc-0081']],
                             columns=['total_extent_km2', 'total_area_km2', 'missing_km2',
                                      'hemisphere', 'filename', 'source_dataset'],
                             index=pd.period_range('2016-07', periods=1, freq='M'))
        return frame

    @patch('seaice.timeseries.monthly')
    def test_month_year_exists_for_date(self, mock_sit):
        mock_sit.return_value = self._sample_frame()
        date = dt.date(2016, 7, 1)
        expected = '5.2'
        actual = config._monthly_data_millions_km2('N', date, 'concentration', None)
        self.assertEqual(expected, actual)

    @patch('seaice.timeseries.monthly')
    def test_month_year_does_not_exist_for_date(self, mock_sit):
        mock_sit.return_value = self._sample_frame()
        date = dt.date(2015, 7, 1)
        expected = ''
        actual = config._monthly_data_millions_km2('N', date, 'concentration', None)
        self.assertEqual(expected, actual)

    @patch('seaice.timeseries.monthly')
    def test_month_year_is_nan_returns_blank(self, mock_sit):
        frame = self._sample_frame()
        frame['total_area_km2'] = np.nan
        mock_sit.return_value = frame
        date = dt.date(2016, 7, 1)
        expected = ''
        actual = config._monthly_data_millions_km2('N', date, 'concentration', None)
        self.assertEqual(expected, actual)

    @patch('seaice.timeseries.monthly')
    def test_total_extent_converts_millions_km2(self, mock_sit):
        mock_sit.return_value = self._sample_frame()
        date = dt.date(2016, 7, 1)
        expected = '8.1'
        actual = config._monthly_data_millions_km2('N', date, 'extent', None)
        self.assertEqual(expected, actual)

    def test_unknown_image_type_raises_error(self):
        date = dt.date(2016, 7, 1)
        with self.assertRaises(SeaIceImagesNotImplementedError):
            config._monthly_data_millions_km2('N', date, 'not_an_image_type', None)

    @patch('seaice.images.config._total_concentration_value')
    def test_anomaly_value(self, mock_total_concentration_value):
        date = dt.date(2016, 7, 1)
        gridset = {}
        mock_total_concentration_value.return_value = 7777777

        actual = config._monthly_data_millions_km2('N', date, 'anomaly', gridset)

        npt.assert_almost_equal(actual, 7.8)


class Test__total_concentration_value(unittest.TestCase):
    @patch('seaice.nasateam.by_name')
    def test_returns_valid_concentration(self, mock_by_name):
        gridset = {'data': np.array([[100, -100],
                                     [255, 33]]),
                   'metadata': {'valid_data_range': (-100, 100),
                                'hemi': 'N'}}
        mock_by_name.return_value = {'grid_areas': np.array([[1, 2],
                                                             [3, 4]])}

        actual = config._total_concentration_value(gridset)

        expected = ((100 * 1) + (-100 * 2) + (33 * 4)) * .01

        npt.assert_almost_equal(actual, expected)


class Test__update_scale_if_hires(unittest.TestCase):

    config = {'canvas': {'scale': 1, 'hires_factor': 1.5}}

    def test_unchanged_if_hires_false(self):
        cfg = copy.deepcopy(self.config)
        cfg.update({'hires': False})
        expected = copy.deepcopy(cfg)
        actual = config._update_scale_if_hires(cfg)
        self.assertEqual(expected, actual)

    def test_unchanged_if_hires_not_present(self):
        cfg = copy.deepcopy(self.config)
        expected = copy.deepcopy(cfg)
        actual = config._update_scale_if_hires(cfg)
        self.assertEqual(expected, actual)

    def test_updated_if_hires_true(self):
        cfg = copy.deepcopy(self.config)
        cfg.update({'hires': True})
        expected = copy.deepcopy(cfg)
        expected['canvas']['scale'] = 1.5
        actual = config._update_scale_if_hires(cfg)
        self.assertEqual(expected, actual)

    def test_uses_default_value_if_hires_true_and_hires_factor_not_present(self):
        cfg = copy.deepcopy(self.config)
        cfg['canvas'].pop('hires_factor')
        cfg.update({'hires': True})
        expected = copy.deepcopy(cfg)
        expected['canvas']['scale'] = 2
        actual = config._update_scale_if_hires(cfg)
        self.assertEqual(expected, actual)
