"""Reformats daily seaice data into regional xls file

This is for internal use by scientists.
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
    fn = '{}_Sea_Ice_Index_Regional_Daily_Data_G02135_{}.xlsx'.format(
        hemi,
        nt.VERSION_STRING
    )
    return os.path.join(output_directory, fn)


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def regional_daily(input_directory, output_directory):
    data_store = os.path.join(input_directory, 'daily.p')

    for hemisphere in (nt.NORTH, nt.SOUTH):
        hemi = hemisphere['short_name']
        output_file = open(output_filepath(output_directory, hemi=hemi), 'wb')

        # Generate the daily dataframe with regional columns
        daily = sit.daily(hemi, data_store=data_store, columns=[])
        # Keep only regional columns
        regional = daily.drop(nt.DAILY_DEFAULT_COLUMNS, axis=1)

        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

        extent_and_area_columns = [c for c in regional.columns if 'missing' not in c]
        extent_and_area_columns.sort()

        for col in extent_and_area_columns:
            regional_mask_cfg, region_prefix = \
                    util.regional_mask_cfg_from_column_name(col)

            # Don't add column to the sheet if wrong hemisphere
            if regional_mask_cfg['hemisphere'] != hemisphere['long_name']:
                continue

            df = regional[col].rolling(window=5, min_periods=2).mean()
            df = pd.DataFrame(df).set_index(
                     [df.index.year, df.index.month, df.index.day]
                 ).unstack(0)

            df.index.names = ['month', 'day']
            df.index = df.index.set_levels(cal.month_name[1:], level=0)

            # Strip the regional mask prefix from the column name
            col = col[len(region_prefix):]

            sheet_name = util.regional_sheet_name(col)
            write_sheet(writer, df, sheet_name)

        writer = util.add_documentation_sheet(
            writer,
            util.documentation_file(output_filepath('', hemi=hemi))
        )

        writer.save()
        log.info('regional_daily created: {}'.format(output_file.name))


def write_sheet(writer, df, sheet_name):
    df.columns = df.columns.droplevel(0)
    df.to_excel(writer, sheet_name, float_format='%.3f')


if __name__ == '__main__':
    regional_daily()
