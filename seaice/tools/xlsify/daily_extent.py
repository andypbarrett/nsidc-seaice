import calendar
from collections import OrderedDict
import os

import click
import pandas as pd

from . import util
from .. import warp
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit

log = seaicelogging.init('seaice.tools')


def output_filename(output_directory):
    return os.path.join(output_directory,
                        'Sea_Ice_Index_Daily_Extent_G02135_{}.xlsx'.format(nt.VERSION_STRING))


def get_climatological_means(df, variable, years):
    clim = df[(df.index.year >= years[0]) &
              (df.index.year <= years[1])].copy()
    return clim.groupby([clim.index.month, clim.index.day])[variable].mean()


def clim_string(years=nt.DEFAULT_CLIMATOLOGY_YEARS):
    return '{0}-{1}'.format(years[0], years[1])


def compute_anomaly(df, clim):
    anomaly = df.copy()

    for i in range(0, anomaly.columns.size):
        anomaly.iloc[:, i] = anomaly.iloc[:, i] - clim
    return anomaly


def month_names():
    return [calendar.month_name[x] for x in range(1, 13)]


# process a DataFrame with data for a single hemisphere, or the "global" region
def process_region(df):
    daily = df.set_index([df.index.month, df.index.day, df.index.year]).unstack(2)['extent']
    daily_clim = get_climatological_means(df, 'interpolated_extent', nt.DEFAULT_CLIMATOLOGY_YEARS)
    five_day = df.set_index([df.index.month, df.index.day, df.index.year]).unstack(2)['5-day']
    five_day_clim = get_climatological_means(df, '5-day', nt.DEFAULT_CLIMATOLOGY_YEARS)

    five_day_daily_change = df['5-day'].diff(periods=1)
    idx = five_day_daily_change.index
    five_day_daily_change = five_day_daily_change.to_frame().set_index(
        [idx.month, idx.day, idx.year]).unstack(2)
    five_day_daily_change.columns = five_day_daily_change.columns.droplevel(0)

    anomaly = compute_anomaly(five_day, five_day_clim)

    daily[' '] = None
    daily[clim_string()] = daily_clim

    five_day[' '] = None
    five_day[clim_string()] = five_day_clim

    daily.index = daily.index.set_levels(month_names(), level=0)
    five_day.index = five_day.index.set_levels(month_names(), level=0)
    five_day_daily_change.index = five_day_daily_change.index.set_levels(month_names(), level=0)
    anomaly.index = anomaly.index.set_levels(month_names(), level=0)

    data = OrderedDict([('Daily-Extent', daily),
                        ('5-Day-Extent', five_day),
                        ('5-Day-Anomaly', anomaly),
                        ('5-Day-Daily-Change', five_day_daily_change)])
    return data


def format_sheets(writer, sheets):
    workbook = writer.book
    # add colors blue with blue
    format1 = workbook.add_format({'bg_color':   '#CEC7FF',
                                   'font_color': '#06009C'})

    # add colors red with red
    format2 = workbook.add_format({'bg_color':   '#FFC7CE',
                                   'font_color': '#9C0006'})

    for sheet in sheets:
        worksheet = writer.sheets[sheet]
        worksheet.conditional_format('C2:ZZ369', {'type':     'cell',
                                                  'criteria': '>',
                                                  'value':    0,
                                                  'format':   format1})

        worksheet.conditional_format('C2:ZZ369', {'type':     'cell',
                                                  'criteria': '<',
                                                  'value':    0,
                                                  'format':   format2})


def write_hemi(writer, df):
    data = process_region(df)
    hemi_id = '{0}H'.format(df['hemisphere'].dropna()[0].capitalize())

    def sheet_name(key):
        return '{0}-{1}'.format(hemi_id, key)

    for key, value in data.items():
        # Remove index names from dataframes so they do not show up in the excel files.
        value.index.names = [None, None]

        value.to_excel(writer, sheet_name(key), float_format='%.3f')

    sheet_names = [sheet_name(key) for key in data.keys()]

    format_sheets(writer, sheet_names[-2:])


def sea_ice_daily_statistics_with_frames(output_directory, north, south):
    output_fn = output_filename(output_directory)

    writer = pd.ExcelWriter(output_fn, engine='xlsxwriter')
    for hemi in [north, south]:
        write_hemi(writer, hemi)

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_filename('')))

    writer.save()
    log.info('sea_ice_daily_statistics created: %s', output_fn)


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False))
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False))
@seaicelogging.log_command(log)
def daily_extent(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'daily.p')
    north = warp.modified_extents(sit.daily('N', data_store=input_file))
    south = warp.modified_extents(sit.daily('S', data_store=input_file))

    sea_ice_daily_statistics_with_frames(output_directory, north, south)


if __name__ == '__main__':
    daily_extent()
