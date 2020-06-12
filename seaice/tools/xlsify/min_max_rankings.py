import calendar
import datetime as dt
import os

import click
import pandas as pd

from . import util
from .. import warp
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def min_max_rankings(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'daily.p')
    north = warp.modified_extents(sit.daily('N', data_store=input_file))
    south = warp.modified_extents(sit.daily('S', data_store=input_file))

    sea_ice_min_max_rankings(output_directory, north, south)


def output_filename(output_directory):
    return os.path.join(output_directory,
                        'Sea_Ice_Index_Min_Max_Rankings_G02135_{}.xlsx'.format(nt.VERSION_STRING))


def min_max_by_month_year(df, variable):
    groupby = [df.index.year, df.index.month]

    minidx = df.loc[df.groupby(groupby)[variable].idxmin()][variable].to_frame()
    maxidx = df.loc[df.groupby(groupby)[variable].idxmax()][variable].to_frame()
    return {'min': minidx, 'max': maxidx}


def add_rank(df, rank_by_variable, ascending):
    df['rank'] = df.groupby(df.index.month)[rank_by_variable].rank(ascending=ascending,
                                                                   method='first')
    return df


def rank_this_variable_monthly_data(df, variable):
    var = min_max_by_month_year(df, variable)
    var['max'] = add_rank(var['max'], variable, ascending=False)
    var['min'] = add_rank(var['min'], variable, ascending=True)
    return var


def rank_monthly_data(df):
    # exclude the current month and October 1978; we want to compare data only
    # for completed months
    monthly_beginning = nt.BEGINNING_OF_SATELLITE_ERA_MONTHLY.strftime('%Y-%m-%d')
    first_of_this_month = dt.date.today().replace(day=1).strftime('%Y-%m-%d')
    df = df[(monthly_beginning <= df.index) & (df.index < first_of_this_month)]

    extent = rank_this_variable_monthly_data(df, 'extent')
    five_day = rank_this_variable_monthly_data(df, '5-day')
    return {'extent': extent, '5-Day': five_day}


def do_annual_min_max_ranking(df, variable):
    min_index = df.groupby([df.index.year])[variable].idxmin()
    max_index = df.groupby([df.index.year])[variable].idxmax()
    mindata = df.loc[min_index][variable].to_frame()
    mindata['rank'] = mindata[variable].rank(ascending=True, method='first')
    maxdata = df.loc[max_index][variable].to_frame()
    maxdata['rank'] = maxdata[variable].rank(ascending=False, method='first')

    mindata['date'] = [date_.strftime('%Y-%m-%d') for date_ in mindata.index]
    maxdata['date'] = [date_.strftime('%Y-%m-%d') for date_ in maxdata.index]
    mindata = mindata.set_index(mindata.index.year)
    maxdata = maxdata.set_index(maxdata.index.year)

    maxdata = maxdata.add_prefix('max-')
    mindata = mindata.add_prefix('min-')

    data = pd.concat([mindata, maxdata], axis=1, sort=True)

    data.index.name = None
    return data


def rank_annual_data(df):
    # exclude 1978 and the current year; 1978 has no data before October, and we
    # want to compare data only for completed years
    first_of_earliest_year = nt.BEGINNING_OF_SATELLITE_ERA_YEARLY.strftime('%Y-%m-%d')
    first_of_this_year = dt.date.today().replace(month=1, day=1).strftime('%Y-%m-%d')
    df = df[(first_of_earliest_year <= df.index) & (df.index < first_of_this_year)]

    annual_daily = do_annual_min_max_ranking(df, 'extent')
    annual_five_day = do_annual_min_max_ranking(df, '5-day')
    return {'daily': annual_daily, '5-Day': annual_five_day}


def monthly_sheet_name(id_string, the_type, mm):
    if the_type == '5-Day':
        the_type = '5-Day-Extent'
    elif the_type == 'extent':
        the_type = 'Daily-Extent'

    return '{0}H-{1}-{2}'.format(id_string[0].upper(),
                                 the_type.title(),
                                 mm.title())


def annual_sheet_name(id_string, the_type):

    return '{0}H-Annual-{1}-Extent'.format(id_string[0].upper(), the_type.title())


def swap_column_level_and_sort(df):
    df.columns = df.columns.swaplevel(1, 0)
    df = df.sort_index(level=0, axis=1)
    return df


def month_names():
    return [calendar.month_name[x] for x in range(1, 13)]


# set index to year and month and then broadcast month back across the columns.
# next swap and sort so that you have the data grouped under the month.
def prepare_monthly(df):
    df['date'] = [date_.strftime('%Y-%m-%d') for date_ in df.index]
    df['month'] = df.index.month
    df = df.set_index(['rank', 'month']).unstack('month')
    df = swap_column_level_and_sort(df)
    df.columns = df.columns.set_levels(month_names(), level=0)
    return df


def write_all_monthly_data(writer, the_dict, id_string):
    types = ['5-Day', 'extent']
    for the_type in types:
        for mm in ['min', 'max']:
            sheet_name = monthly_sheet_name(id_string, the_type, mm)
            df = the_dict[the_type][mm]
            df = prepare_monthly(df)

            if the_type == 'extent':
                df = df.reindex(['extent', 'date'], axis=1, level=1)

            df.to_excel(writer, '{sheet}'.format(sheet=sheet_name), float_format='%.3f')


def write_all_annual_data(writer, the_dict, id_string):
    types = ['5-Day', 'daily']
    for the_type in types:
        sheet_name = annual_sheet_name(id_string, the_type)
        df = the_dict[the_type]
        df.to_excel(writer, '{sheet}'.format(sheet=sheet_name), float_format='%.3f')


def resize_columns(writer):
    start_col = 0
    stop_col = 100
    width = 10
    for sheetname, sheet in writer.sheets.items():
        sheet.set_column(start_col, stop_col, width)


def sea_ice_min_max_rankings(output_directory, north, south):
    '''
    Find and read the standard daily CSV files and write an output xlsx file
    containing each month's max and min extent ordered by rank.
    also collapse the information to provide annual min and max extent rankings.
    '''
    output_fn = output_filename(output_directory)
    writer = pd.ExcelWriter(output_fn, engine='xlsxwriter')
    for hemi, hemi_id in zip([north, south], nt.VALID_HEMISPHERES):
        month_data = rank_monthly_data(hemi)
        annual_data = rank_annual_data(hemi)
        write_all_monthly_data(writer, month_data, hemi_id)
        write_all_annual_data(writer, annual_data, hemi_id)
        resize_columns(writer)

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_filename('')))

    writer.save()
    log.info('min_max_rankings created %s', output_fn)


if __name__ == '__main__':
    min_max_rankings()
