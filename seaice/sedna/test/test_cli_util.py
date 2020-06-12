import os
import unittest

import seaice.sedna.cli.util as util


class Test_load_config(unittest.TestCase):

    def test_returns_empty_with_default_configfile_which_does_not_exist(self):
        assert not os.path.exists(util.DEFAULT_CONFIG_FILE)

        actual = util.load_config(util.DEFAULT_CONFIG_FILE)

        self.assertEqual(actual, {})
