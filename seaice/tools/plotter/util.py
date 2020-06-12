import logging
import time

import plotly
import plotly.plotly as py

from seaice.tools.errors import SeaIceToolsRuntimeError


log = logging.getLogger(__name__)


def save_plot(cmd, *args, **kwargs):
    attempts = 0
    max_attempts = 10

    while attempts < max_attempts:
        try:
            py.image.save_as(*args, **kwargs)
            log.info('{} created: {}'.format(cmd, args[1]))
            break
        except plotly.exceptions.PlotlyError as err:
            attempts += 1
            log.warning('Plotly Error: {}'.format(err))
            time.sleep(1)

    if attempts == max_attempts:
        msg = 'Failed to save image with arguments: {}, {}'.format(args, kwargs)
        log.error(msg)
        raise SeaIceToolsRuntimeError(msg)
