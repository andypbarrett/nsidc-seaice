import calendar
import os

import click
import pandas as pd

from . import util
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')

clim_string = '{0}-{1}'.format(*nt.DEFAULT_CLIMATOLOGY_YEARS)


def month_dict():
    m_dict = {}
    for i in range(1, 13):
        m_dict[i] = calendar.month_name[i]
    return m_dict


def output_filename():
    '''
    Sea_Ice_Index_Rates_of_Change_G02135_v3.0.xlsx
    '''
    return 'Sea_Ice_Index_Rates_of_Change_G02135_{}.xlsx'.format(nt.VERSION_STRING)


def get_missing_values(df):
    '''
    By looking that the number of interpolated days is equal to the last()
    day value we find missing data.
    '''
    a = df.groupby([df.index.year, df.index.month])
    missing = a['interpolated_extent'].count() == a['day'].last()
    return missing


def add_formatting(writer, sheet):
    workbook = writer.book
    # add colors blue with blue
    format1 = workbook.add_format({'bg_color': '#CEC7FF', 'font_color': '#06009C'})
    # add colors red with red
    format2 = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

    worksheet = writer.sheets[sheet]
    worksheet.conditional_format('B3:ZZ369', {'type':     'cell',
                                              'criteria': '>',
                                              'value':    0,
                                              'format':   format1})

    worksheet.conditional_format('B3:ZZ369', {'type':     'cell',
                                              'criteria': '<',
                                              'value':    0,
                                              'format':   format2})


def round_for_output(df_in, cols, rounding):
    df = df_in.copy()
    for col, rnd in zip(cols, rounding):
        df[col] = df[col].round(rnd)
    return df


def write_monthly_trends(writer, df_in, clim_in):
    bottom_offset = 3

    # names of columns in df_in
    columns = [u'Ice change in Mkm^2 per month',
               u'Ice change in km^2 per day',
               u'Ice change in mi^2 per month',
               u'Ice change in mi^2 per day']

    # names for sheets corresponding to the column names
    sheets = [u'Ice-Change-Mkm^2-per-Month',
              u'Ice-Change-km^2-per-Day',
              u'Ice-Change-mi^2-per-Month',
              u'Ice-Change-mi^2-per-Day']

    rounding = [3, -2, -3, -2]
    df = round_for_output(df_in, columns, rounding)
    clim = round_for_output(clim_in, columns, rounding)

    hemi_id = '{0}H'.format(df['hemisphere'].dropna().iloc[0])

    df = df.unstack(1)
    df = df.rename(columns=month_dict())

    df.index.name = None

    for column, sheet in zip(columns, sheets):
        sheet_name = '{0}-{1}'.format(hemi_id, sheet)
        df[column].to_excel(writer, sheet_name, float_format='%.3f',
                            startrow=1, startcol=0)
        writer.sheets[sheet_name].write_string(0, 0,
                                               '{} from 5-day averaged daily values'.format(column))
        clim[column].name = clim_string
        clim[column].to_frame().T.to_excel(writer, sheet_name,
                                           header=False,
                                           startrow=df[column].index.size + bottom_offset,
                                           float_format='%.3f')

        add_formatting(writer, sheet_name)


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def rates_of_change(input_directory, output_directory):
    """
    input_directory: directory with Daily sedna csv file 'daily.p'
    """
    input_file = os.path.join(input_directory, 'daily.p')

    north = sit.monthly_rates_of_change('N', data_store=input_file)
    north_clim = sit.climatology_average_rates_of_change('N', data_store=input_file)
    south = sit.monthly_rates_of_change('S', data_store=input_file)
    south_clim = sit.climatology_average_rates_of_change('S', data_store=input_file)

    columns = {'ice change Mkm^2 per month': 'Ice change in Mkm^2 per month',
               'ice change km^2 per day': 'Ice change in km^2 per day',
               'ice change mi^2 per month': 'Ice change in mi^2 per month',
               'ice change mi^2 per day': 'Ice change in mi^2 per day'}

    north = north.rename(columns=columns)
    north_clim = north_clim.rename(columns=columns)
    south = south.rename(columns=columns)
    south_clim = south_clim.rename(columns=columns)

    sea_ice_daily_csv_to_trend_xls(output_directory, north, south, north_clim, south_clim)


def sea_ice_daily_csv_to_trend_xls(output_directory, north, south, north_clim, south_clim):
    """
    Transform datataframes from daily CSV files into monthly ice change trends.

    output_directory: output directory to write output file
    """
    output_file = os.path.join(output_directory, output_filename())

    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

    write_monthly_trends(writer, north, north_clim)
    write_monthly_trends(writer, south, south_clim)

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_filename()))

    writer.save()
    log.info('rates_of_change created: %s', output_file)


if __name__ == '__main__':
    rates_of_change()
