import cProfile
import datetime as dt
import os
from itertools import product

from seaice.images.api import ice_image
from seaice.data import locator
import seaice.nasateam as nt


THIS_DIR = os.path.dirname(os.path.realpath(__file__))

cfg_path = os.path.join(THIS_DIR,
                        'test_config.yml')

hemis = ['N', 'S']
dates = [
    dt.date(2019, 8, 1),
    dt.date(2019, 7, 1),
    dt.date(2018, 12, 1),
]

img_kwargs = {
    'image_labels': [],
    'sub-title': {'text': ''},
    'source_attribution': {'text': ''},
    'image': {'locations': [], 'locations_text_kwargs': []},
}

if __name__ == '__main__':
    locator._find_all_nasateam_ice_files_multiple_paths(nt.DEFAULT_SEA_ICE_PATHS)

    pr = cProfile.Profile()
    pr.enable()
    for idx, (hemi, date) in enumerate(product(hemis, dates)):
        ice_image(
            hemi,
            date,
            temporality='monthly',
            image_type='trend',
            output=os.path.join(THIS_DIR, 'profile/', 'test.png'),
            year_range=(1979, 2019),
            config_filename=cfg_path,
            trend_start_year=1979,
            **img_kwargs,
        )
    pr.disable()

    """
    visualize output with `snakeviz`, e.g.:

        snakeviz -s -H 0.0.0.0 -p 8080 profile/
    """
    pr.dump_stats(os.path.join(THIS_DIR, 'profile', 'out.prof'))
