import os

import seaice.nasateam as nt


def this_dir():
    return os.path.dirname(os.path.abspath(__file__))


def parent_dir():
    return os.path.dirname(this_dir())


def default_config_dir():
    return os.path.join(parent_dir(), 'seaice.tools', 'configs')


def output_image_dir():
    return os.path.join(parent_dir(), 'test_output_images')


def output_dir():
    return os.path.join(parent_dir(), 'test_output')


def data_dir():
    return os.path.join(parent_dir(), 'data', 'xlsify')


def datastore_directory():
    return nt.DATA_STORE_BASE_DIRECTORY
