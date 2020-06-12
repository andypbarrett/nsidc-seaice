import os


# WARNING: Ensure all regional mask names do not include any other regional
# mask names, e.g. "regionA" and "regionAB" would be in conflict.
# `regional_mask_cfg_from_column_name` lookup behavior is the reason for this.
DEFAULT_REGIONAL_MASKS = [
    {
        'name': 'meier2007',
        'file': os.path.realpath(
            os.path.join(os.path.dirname(__file__),
                         'pkg_data/masks/Arctic_region_mask_Meier_AnnGlaciol2007.msk')),
        'hemisphere': 'north',
        'regions': {
            'okhotsk': 2,
            'bering': 3,
            'hudson': 4,
            'stlawrence': 5,
            'baffin': 6,
            'greenland': 7,
            'barents': 8,
            'kara': 9,
            'laptev': 10,
            'eastsiberian': 11,
            'chukchi': 12,
            'beaufort': 13,
            'canadianarchipelago': 14,
            'centralarctic': 15
        }
    },
    {
        'name': 'region_s',
        'file': os.path.realpath(
            os.path.join(os.path.dirname(__file__),
                         'pkg_data/masks/Antarctic_region_mask.msk')),
        'hemisphere': 'south',
        'regions': {
            'weddell': 2,
            'indian': 3,
            'pacific': 4,
            'ross': 5,
            'bellingshausen amundsen': 6
        }
    }
]
