"""Reformats monthly seaice data into regional xls file

This is for internal use by scientists.

output includes extents and ranks

"""
import calendar as cal
import os

import click
import pandas as pd

from . import util
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')


def output_filepath(output_directory, *, hemi):
    fn = '{}_Sea_Ice_Index_Regional_Monthly_Data_G02135_{}.xlsx'.format(
        hemi,
        nt.VERSION_STRING
    )
    return os.path.join(output_directory, fn)


def column_identifier(col_name):
    if 'extent' in col_name:
        id = 'extent'
    else:
        id = 'area'
    return id


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def regional_monthly(input_directory, output_directory):
    data_store = os.path.join(input_directory, 'monthly.p')

    for hemisphere in nt.NORTH, nt.SOUTH:
        hemi = hemisphere['short_name']
        output_file = open(output_filepath(output_directory, hemi=hemi), 'wb')

        monthly = sit.monthly(hemi, data_store=data_store, columns=[])
        regional = monthly.drop(nt.MONTHLY_DEFAULT_COLUMNS, axis=1)

        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

        extent_and_area_columns = [c for c in regional.columns if 'missing' not in c]
        extent_and_area_columns.sort()

        for col in extent_and_area_columns:
            regional_mask_cfg, region_prefix = \
                    util.regional_mask_cfg_from_column_name(col)

            # Don't add column to the sheet if wrong hemisphere
            if regional_mask_cfg['hemisphere'] != hemisphere['long_name']:
                continue

            df = regional[col]
            df.name = column_identifier(col)
            df = pd.DataFrame(df).set_index([df.index.month, df.index.year]).unstack(0)

            # Add Ranks for each column
            for idx, mcol in enumerate(df.columns):
                new_index = ('rank', mcol[1])
                df[new_index] = df[mcol].rank()

            # Strip the regional mask prefix from the column name
            col = col[len(region_prefix):]

            df.columns = df.columns.swaplevel(0, 1)
            df = df.sort_index(axis=1, level=0)
            df.columns = df.columns.set_levels(cal.month_name[1:], level=0)

            df.columns.names = [None, None]
            df.index.name = None

            sheet_name = util.regional_sheet_name(col)
            write_sheet(writer, df, sheet_name)

        writer = util.add_documentation_sheet(
            writer,
            util.documentation_file(output_filepath('', hemi=hemi))
        )

        writer.save()
        log.info('regional_monthly created: %s', output_file.name)


def write_sheet(writer, df, sheet_name):
    df.to_excel(writer, sheet_name, float_format='%.3f')


if __name__ == '__main__':
    regional_monthly()
