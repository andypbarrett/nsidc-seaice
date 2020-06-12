"""This package provides functions to access daily and monthly nasateam sea ice
concentrations.

Full documentation on the datasets can be found at:
- https://nsidc.org/data/docs/daac/nsidc0051_gsfc_seaice.gd.html
- https://nsidc.org/data/docs/daac/nsidc0081_ssmi_nrt_seaice.gd.html

"""
import logging

from .api import concentration_daily  # noqa
from .api import concentration_daily_average_over_date_range  # noqa
from .api import concentration_monthly  # noqa
from .api import concentration_monthly_anomaly  # noqa
from .api import concentration_monthly_trend  # noqa
from .api import concentration_seasonal_trend  # noqa
from .api import extent_daily  # noqa
from .api import extent_daily_median  # noqa
from .api import extent_monthly  # noqa
from .api import extent_monthly_median  # noqa
from .errors import SeaIceDataException  # noqa
from .errors import SeaIceDataNoData  # noqa
from . import gridset_filters as filters  # noqa
from .version import VERSION as __version__  # noqa

__all__ = [
    'concentration_daily',
    'concentration_monthly',
    'extent_daily',
    'extent_daily_median',
    'extent_monthly',
    'extent_monthly_median',
    'SeaIceDataException',
    'SeaIceDataNoData',
    'filters'
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
