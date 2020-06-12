import logging

from .api import daily  # noqa
from .api import monthly  # noqa
from .api import daily  # noqa
from .api import monthly  # noqa
from .api import monthly_rates_of_change  # noqa
from .api import climatology_average_rates_of_change  # noqa
from .api import nday_average  # noqa
from .api import scale  # noqa
from .api import normal_statistics  # noqa
from .api import quantiles  # noqa
from .api import monthly_anomaly  # noqa
from .api import monthly_percent_anomaly  # noqa
from .api import trend  # noqa
from .api import climatology_means  # noqa

logging.getLogger(__name__).addHandler(logging.NullHandler())
