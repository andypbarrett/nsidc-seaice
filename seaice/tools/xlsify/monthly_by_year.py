import calendar
from itertools import product
import os

import click
import numpy as np
import pandas as pd

from . import util
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit

log = seaicelogging.init('seaice.tools')


def output_filename(output_directory):
    return os.path.join(output_directory,
                        'Sea_Ice_Index_Monthly_Data_by_Year_G02135_{}.xlsx'.format(
                            nt.VERSION_STRING))


def monthly_by_year_with_frames(output_directory, north, south):
    output_fn = output_filename(output_directory)

    writer = pd.ExcelWriter(output_fn, engine='xlsxwriter')
    for hemi in [north, south]:
        write_hemi(writer, hemi)

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_filename('')))

    writer.save()
    log.info('daily_extent created: %s', output_fn)


def write_hemi(writer, df):
    hemi_id = '{0}H'.format(df['hemisphere'].dropna()[0].capitalize())

    write_sheet(df, writer, 'total_extent_km2', '{}-Extent'.format(hemi_id))
    write_sheet(df, writer, 'total_area_km2', '{}-Area'.format(hemi_id))


def write_sheet(df, writer, column, sheet_name):
    df = df[column].unstack(1) / 1e6

    # see if any months are missing before adding the annual value to the
    # dataframe
    missing_months = df.isnull().sum(axis=1)

    annual = _compute_annual_ice_stats(df)

    # blank column between months and the annual value
    df[''] = ''

    df['Annual'] = annual

    df.to_excel(writer, sheet_name, float_format='%.3f')

    # highlight the annual value in red if any months are missing
    red_format = writer.book.add_format({'bg_color':   '#FFC7CE',
                                         'font_color': '#9C0006'})
    red_format.set_num_format('0.000')
    worksheet = writer.book.get_worksheet_by_name(sheet_name)
    for index, count in enumerate(missing_months):
        if count == 0:
            continue

        xlsx_cell = '{}{}'.format('O', index + 2)
        worksheet.write(xlsx_cell, np.round(annual.iloc[index], 3), red_format)


def _compute_annual_ice_stats(df):
    """Returns a np array containing the weighted averages of the given monthly
    data. Weights are the number of days in the month.

    df: data indexed by year; each column contains data for a different month

    """
    # It seems like this should work:
    #
    # weights = np.fromfunction(lambda i, j: calendar.monthrange(i + 1978, j + 1)[1], df.shape)
    #
    # When that's run, the values of i and j passed to monthrange turn out to be
    # full np arrays shaped like df, instead of being iterated over i and j,
    # which is what I thought the point of fromfunction was...anyway we need to
    # iterate ourselves to build up the weights
    weights = np.empty_like(df.values)
    rows, cols = df.values.shape
    for row, col in product(range(rows), range(cols)):
        year = row + df.index[0]
        month = col + 1
        weights[row, col] = calendar.monthrange(year, month)[1]

    weighted_averages = np.ma.average(np.ma.masked_invalid(df.values), axis=1, weights=weights).data

    return pd.Series(weighted_averages, index=df.index)


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def monthly_by_year(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'monthly.p')
    north = get_df('N', data_store=input_file)
    south = get_df('S', data_store=input_file)

    monthly_by_year_with_frames(output_directory, north, south)


def get_df(hemi, data_store):
    df = sit.monthly(hemi, data_store=data_store)
    df = df.set_index([df.index.year, df.index.month])
    df.index = df.index.set_levels(calendar.month_name[1:], level=1)
    df.index.names = [None, None]
    return df


if __name__ == '__main__':
    monthly_by_year()
