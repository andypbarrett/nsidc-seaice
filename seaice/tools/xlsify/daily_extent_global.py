import os

import click
import pandas as pd

from . import util
from .. import warp
from .daily_extent import process_region, format_sheets
import seaice.logging as seaicelogging
import seaice.timeseries as sit

log = seaicelogging.init('seaice.tools')


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def daily_extent_global(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'daily.p')
    north = warp.modified_extents(sit.daily('N', data_store=input_file))
    south = warp.modified_extents(sit.daily('S', data_store=input_file))

    global_cols = ['extent', 'interpolated_extent', '5-day']
    global_ext = north[global_cols] + south[global_cols]

    output_fn = os.path.join(output_directory, 'Global_Daily_Extent_G02135.xlsx')

    writer = pd.ExcelWriter(output_fn, engine='xlsxwriter')
    data = process_region(global_ext)
    for key, value in data.items():
        # Remove index names from dataframes so they do not show up in the excel files.
        value.index.names = [None, None]
        value.to_excel(writer, key, float_format='%.3f')

    format_sheets(writer, list(data.keys())[-2:])

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_fn))
    writer.save()
    log.info('sea_ice_daily_statistics_global created: %s', output_fn)


if __name__ == '__main__':
    daily_extent_global()
