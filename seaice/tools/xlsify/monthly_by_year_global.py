import os

import click
import pandas as pd

from . import util
from .. import warp
from .monthly_by_year import get_df, write_sheet
import seaice.logging as seaicelogging
import seaice.timeseries as sit
from seaice import version_flag

log = seaicelogging.init('seaice.tools')


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@version_flag
@seaicelogging.log_command(log)
def monthly_by_year_global(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'monthly.p')
    north = get_df('N', data_store=input_file)[['total_extent_km2']]
    south = get_df('S', data_store=input_file)[['total_extent_km2']]
    global_extent = north + south
    global_extent.columns = ['extent']

    output_fn = os.path.join(output_directory, 'Global_Monthly_Extent_and_Ranks_G02135.xlsx')

    writer = pd.ExcelWriter(output_fn, engine='xlsxwriter')
    write_sheet(global_extent, writer, 'extent', 'Extents')

    global_extents = sit.scale(global_extent['extent']).unstack(level=1)

    global_extents.rank().to_excel(writer, sheet_name='All Ranks', na_rep='')

    for column in global_extents:
        extents = global_extents[column]

        df = warp.add_rank(pd.DataFrame({'extent': extents}))
        df = df.reset_index()
        df = df[['rank', 'index', 'extent']]
        df.columns = ['rank', 'year', 'extent']
        df = df.sort_values('rank')
        df = df.set_index('rank')

        df.to_excel(writer, column, float_format='%.3f')

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_fn))

    writer.save()
    log.info('daily_extent created: %s', output_fn)


if __name__ == '__main__':
    monthly_by_year_global()
