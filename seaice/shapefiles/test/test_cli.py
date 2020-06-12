import copy
import datetime as dt
import unittest

import seaice.shapefiles.cli.sii_shp as cli
from seaice.shapefiles.errors import SeaIceShapefilesError


# click flags; click ensures that these keys are present; we don't really
# care about them for most of the tests, but they will always be present in our
# application logic
#
# monthly and polygon are set to True so that the validator does not break
# unrelated tests, and tests for the validator can focus on specific properties
CONFIG_FLAGS = {
    'monthly': True,
    'daily': False,
    'polygon': True,
    'polyline': False,
    'all': False,
    'median': False,
    'debug_config': False
}


class Test__set_defaults_temporal(unittest.TestCase):

    def test_doesnt_change_when_month_is_set(self):
        conf = {
            'all': False,
            'median': False,
            'month': 5
        }
        expected = copy.deepcopy(conf)
        actual = cli._set_defaults_temporal(conf)
        self.assertEqual(expected, actual)

    def test_sets_latest_with_no_temporal_keys(self):
        conf = {
            'all': False,
            'median': False
        }
        expected = copy.deepcopy(conf)
        expected['latest'] = 1
        actual = cli._set_defaults_temporal(conf)
        self.assertEqual(expected, actual)

    def test_sets_all_with_no_temporal_keys_and_median(self):
        conf = {
            'all': False,
            'median': True
        }
        expected = copy.deepcopy(conf)
        expected['all'] = True
        actual = cli._set_defaults_temporal(conf)
        self.assertEqual(expected, actual)


class Test__process_cli_config(unittest.TestCase):
    def test_adds_hemisphere_nt_north(self):
        cli_config = {'hemi': 'N'}
        cli_config.update(CONFIG_FLAGS)

        config = cli._process_cli_config(cli_config)
        actual = config['hemis'][0]['short_name']
        expected = 'N'

        self.assertEqual(expected, actual)

    def test_adds_hemisphere_nt_south_and_crs(self):
        cli_config = {'hemi': 'S'}
        cli_config.update(CONFIG_FLAGS)

        config = cli._process_cli_config(cli_config)
        actual = config['hemis'][0]['short_name']
        expected = 'S'

        self.assertEqual(expected, actual)

    def test_adds_output_dir(self):
        cli_config = {'hemi': 'N', 'output_dir': '/foo/bar'}
        cli_config.update(CONFIG_FLAGS)
        config = cli._process_cli_config(cli_config)
        actual = config['output_dir']
        expected = '/foo/bar'

        self.assertEqual(expected, actual)

    def test_parses_search_paths(self):
        cli_config = {'hemi': 'N', 'search_paths': '/foo/bar,/alice/bob'}
        cli_config.update(CONFIG_FLAGS)
        config = cli._process_cli_config(cli_config)
        actual = config['search_paths']
        expected = ['/foo/bar', '/alice/bob']

        self.assertEqual(expected, actual)

    def test_raises_error_with_invalid_year_month(self):
        cli_config = {'hemi': 'N', 'year': dt.date.today().year + 1, 'month': 1}
        cli_config.update(CONFIG_FLAGS)

        self.assertRaises(SeaIceShapefilesError, cli._process_cli_config, cli_config)


class Test__validate_config(unittest.TestCase):
    tests = 0

    @classmethod
    def add(cls, test_conf, valid):
        """Add a test method to this class that will be run by nose. The methods are
        named "test_validate_config_$NUM" so they will be run by nose and it is
        clear from the output that they belong to this class.

        If the given conf is valid, the test method should expect no error to be
        raised; if it is invalid, an error is expected.

        Arguments:
        ---------
        test_conf: dict containing config settings. Merged with CONFIG_FLAGS so
            that flag-based issues don't break the tests.

        valid: bool describing whether test_conf is a valid configuration or not

        """
        def test(self):
            config = self.conf(test_conf)
            if valid:
                try:
                    cli._validate_config(config)
                except SeaIceShapefilesError:
                    self.fail('SeaIceShapefilesError raised by _validate_config : {}'.format(
                        str(test_conf)))
            else:
                with self.assertRaises(SeaIceShapefilesError, msg=str(test_conf)):
                    cli._validate_config(config)

        test.__name__ = 'test_validate_config_{num:02}'.format(num=cls.tests)
        cls.tests += 1

        setattr(cls, test.__name__, test)

    def conf(self, conf_in={}):
        """Returns a configuration dict suitable to pass to _validate_config. Because
        the config dict originates from click and certain values are marked as
        flags, _validate_config expects the config to have certain keys. These
        keys are all contained in CONFIG_FLAGS.

        Before merging conf_in with CONFIG_FLAGS, some changes may be made to
        the copy of CONFIG_FLAGS. Based on conf_in, we may implicitly prefer a
        monthly or daily setting, so those keys are set accordingly. Since the
        merge with conf_in happens after this, anything explicitly set on
        conf_in is honored.

        Arguments:
        ----------
        conf_in: dict containing config settings

        """
        config = copy.deepcopy(CONFIG_FLAGS)
        config_in = copy.deepcopy(conf_in)

        if 'daily' in config_in and config_in['daily']:
            config['monthly'] = False
        if 'monthly' in config_in and config_in['monthly']:
            config['daily'] = False
        if ('day' in config_in) or ('dayofyear' in config_in):
            config['daily'] = True
            config['monthly'] = False

        config.update(config_in)

        return config

    def test_debug_config(self):
        """Sets config['error'] instead of raising an exception with debug_config

        """
        config = self.conf({
            'debug_config': True,
            'daily': True,
            'monthly': True
        })

        try:
            cli._validate_config(config)
        except SeaIceShapefilesError:
            self.fail('SeaIceShapefilesError raised by _validate_config : {}'.format(
                str(test_conf)))

        actual = config['errors']
        expected = 'Invalid configuration: Exactly one of --daily or --monthly must be chosen.'
        self.assertEqual(expected, actual)


test_confs = [
    # --year --month
    {'year': dt.date.today().year,
     'month': dt.date.today().month,
     'valid': True},
    {'year': (dt.date.today() + dt.timedelta(32)).year,
     'month': (dt.date.today() + dt.timedelta(32)).month,
     'valid': False},

    # --daily --monthly
    {'daily': True,
     'monthly': False,
     'valid': True},
    {'daily': False,
     'monthly': True,
     'valid': True},
    {'daily': True,
     'monthly': True,
     'valid': False},
    {'daily': False,
     'monthly': False,
     'valid': False},

    # --polygon --polyline
    {'polygon': True,
     'polyline': True,
     'valid': False},
    {'polygon': True,
     'polyline': False,
     'valid': True},
    {'polygon': False,
     'polyline': True,
     'valid': True},
    {'polygon': False,
     'polyline': False,
     'valid': False},

    # --dayofyear with --monthly --daily
    {'monthly': True,
     'daily': False,
     'dayofyear': 175,
     'valid': False},
    {'daily': True,
     'monthly': False,
     'dayofyear': 175,
     'valid': True},

    # --day with --monthly --daily
    {'daily': True,
     'monthly': False,
     'day': 17,
     'valid': True},
    {'monthly': True,
     'daily': False,
     'day': 17,
     'valid': False},

    # --daily --median with temporal options.
    {'daily': True,
     'median': True,
     'valid': False},
    {'daily': True,
     'median': True,
     'day': 5,
     'valid': False},
    {'daily': True,
     'median': True,
     'month': 2,
     'valid': False},

    # --latest with --median
    {'daily': True,
     'median': True,
     'latest': 2,
     'valid': False},
    {'monthly': True,
     'median': True,
     'valid': False},

    # --all with other temporal options
    {'all': True,
     'latest': 5,
     'valid': False},
    {'all': True,
     'dayofyear': 1,
     'valid': False},
    {'all': True,
     'year': 1989,
     'valid': False},
    {'all': True,
     'month': 9,
     'valid': False},
    {'all': True,
     'day': 19,
     'valid': False},
    {'all': True,
     'valid': True},

    # --latest with other temporal options (except those listed above)
    {'latest': 1,
     'dayofyear': 3,
     'valid': False},
    {'latest': 1,
     'year': 1983,
     'valid': False},
    {'latest': 1,
     'month': 5,
     'valid': False},
    {'latest': 1,
     'day': 25,
     'valid': False},
    {'latest': 1,
     'valid': True},

    # --dayofyear with other temporal options (except those listed above)
    {'dayofyear': 205,
     'month': 5,
     'valid': False},
    {'dayofyear': 205,
     'day': 25,
     'valid': False},
    {'dayofyear': 205,
     'year': 1983,
     'valid': True},
    {'dayofyear': 205,
     'valid': True},

    # --year with other temporal options (except those listed above)
    {'year': 1992,
     'valid': True},
    {'year': 1983,
     'month': 12,
     'valid': True},
    {'year': 1983,
     'day': 27,
     'valid': True},

    # --month with other temporal options (except those listed above)
    {'month': 11,
     'day': 25,
     'valid': True},
    {'month': 12,
     'year': 1983,
     'day': 27,
     'valid': True},
    {'month': 12,
     'valid': True},

    # --day with other temporal options (except those listed above)
    {'day': 27,
     'valid': True},

    # --monthly --date_range
    {'median': False,
     'date_range': (dt.date(2010, 1, 1), dt.date(2011, 1, 1)),
     'valid': True},

    # --monthly, --year, and --date_range (cannot use --year with --date_range)
    {'median': False,
     'year': 2010,
     'date_range': (dt.date(2010, 1, 1), dt.date(2011, 1, 1)),
     'valid': False},

    # --median --monthly --date_range (cannot use --median with --date_range)
    {'median': True,
     'date_range': (dt.date(2010, 1, 1), dt.date(2011, 1, 1)),
     'valid': False}
]

for test_conf in test_confs:
    valid = test_conf.pop('valid')
    Test__validate_config.add(test_conf, valid)
