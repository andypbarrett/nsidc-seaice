import calendar
import os

import click
import pandas as pd
from pandas import ExcelWriter

from . import util
from .. import warp
import seaice.nasateam as nt
import seaice.timeseries as sit
import seaice.logging as seaicelogging

log = seaicelogging.init('seaice.tools')


def output_filename():
    ''' Convert SII filename to output filename
    'Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_v3.0.xlsx'
    '''
    return 'Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_{}.xlsx'.format(nt.VERSION_STRING)


def header(data, mean):
    """Returns header values for a monthly dataframe with a period index"""

    the_max = data[data['rank'] == data['rank'].max()]
    the_min = data[data['rank'] == data['rank'].min()]
    this_year = data[data['year'] == data['year'].max()]

    month_name = this_year.index.to_timestamp()[0].strftime('%B')
    current_year = this_year.index.to_timestamp()[0].strftime('%Y')
    max_year = the_max.index.to_timestamp()[0].strftime('%Y')
    min_year = the_min.index.to_timestamp()[0].strftime('%Y')

    the_extent = this_year['extent'].values[0]
    the_rank = this_year['rank'].values[0]
    the_trend = this_year['trend-through-year-km^2-per-year'].values[0]
    the_pct_trend = this_year['%-trend-through-year'].values[0]

    max_extent = the_max['extent'].values[0]
    min_extent = the_min['extent'].values[0]

    mean_clim_diff = round((the_extent - mean), 2) * 1000000
    max_extent_diff = round((the_extent - max_extent), 2)*1000000
    min_extent_diff = round((the_extent - min_extent), 2)*1000000

    out_headers = [
        '{month} {cur_year} extent: {cur_extent:.2f} Mkm^2',
        '{month} {clim_start_year}-{clim_stop_year} mean extent: {clim_mean:.2f} Mkm^2',
        ('{month} {cur_year} - {month} {clim_start_year}-{clim_stop_year}:'
         ' {cur_extent_clim_mean_diff:-0.0f} km^2'),
        '{month} {cur_year} rank: {the_rank}; {num_higher} higher, {num_lower} lower',
        ('{month} {max_year} (max): {max_extent:.2f} Mkm^2;'
         ' diff: {max_extent_diff:-.0f} km^2'),
        ('{month} {min_year} (min): {min_extent:.2f} Mkm^2;'
         ' diff: {min_extent_diff:-.0f} km^2'),
        '{month} {cur_year} trend: {cur_trend_prct:-.2f} percent/decade',
        '{month} {cur_year} trend: {cur_trend_extent:-.0f} km^2/year']

    fmt = {'month': month_name,
           'cur_year': current_year,
           'cur_extent': the_extent,
           'clim_start_year': nt.DEFAULT_CLIMATOLOGY_YEARS[0],
           'clim_stop_year': nt.DEFAULT_CLIMATOLOGY_YEARS[1],
           'clim_mean': mean,
           'cur_extent_clim_mean_diff': mean_clim_diff,
           'the_rank': the_rank,
           'num_higher': len(data)-the_rank,
           'num_lower': the_rank-1,
           'max_year': max_year,
           'max_extent': max_extent,
           'max_extent_diff': max_extent_diff,
           'min_year': min_year,
           'min_extent': min_extent,
           'min_extent_diff': min_extent_diff,
           'cur_trend_prct': the_pct_trend,
           'cur_trend_extent': the_trend}

    out_headers = [line.format(**fmt) for line in out_headers]

    return out_headers


def read_monthly_sea_ice_file(filename):
    '''
    Read the current monthly sea ice index data files. e.g. 'N_05_area.txt'
    This uses the header to define columns (but renames mo and region), it
    also skips any extra lines that don't fit the column definition ignoring
    any extra data following any good data.
    '''
    data = pd.read_csv(filename, error_bad_lines=False,
                       warn_bad_lines=False,
                       skipinitialspace=True,
                       delimiter='\s+')
    data.rename(columns={'mo': 'month', 'region': 'hemisphere'}, inplace=True)
    data = data.dropna()

    return data


def sheet_name(joined_data):
    return '-'.join([calendar.month_name[int(joined_data['month'].iloc[0])],
                     joined_data['hemisphere'].iloc[0] + 'H'])


def write_output_xlsx(the_writer, output_headers, joined_data):
    """
    the_writer = an open xlswriter:ExcelWriter
    output_headers - stats and infor for the first few lines of the spreadsheet
    joined_data - DataFrame
    """
    sheet = sheet_name(joined_data)

    joined_data.to_excel(the_writer, sheet, float_format='%.3f',
                         startrow=len(output_headers)+1, startcol=0)
    for i, header in enumerate(output_headers):
        the_writer.sheets[sheet].write_string(i, 0, header)


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False),
                default=nt.DATA_STORE_BASE_DIRECTORY)
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False),
                default=os.path.join(nt.SEA_ICE_BASE_DIR, 'xlsx'))
@seaicelogging.log_command(log)
def monthly_with_statistics(input_directory, output_directory):
    input_file = os.path.join(input_directory, 'monthly.p')

    output_file = os.path.join(output_directory, output_filename())

    north_df = sit.monthly('N', data_store=input_file)
    south_df = sit.monthly('S', data_store=input_file)

    north_df = warp.seaicetimeseries_df_to_monthly_sea_ice_index_df(north_df)
    south_df = warp.seaicetimeseries_df_to_monthly_sea_ice_index_df(south_df)

    month_list = list(range(1, 12 + 1))
    north_monthly_dfs = warp.split_by_column(north_df, 'month', values=month_list)
    south_monthly_dfs = warp.split_by_column(south_df, 'month', values=month_list)

    writer = ExcelWriter(output_file, engine='xlsxwriter')
    for month_data in (north_monthly_dfs + south_monthly_dfs):
        month_data = warp.add_rank(month_data)
        mean = warp.climatology_mean_extent(month_data)
        month_data = warp.add_extent_climatology(month_data, mean)
        month_data = warp.add_trends(month_data, mean)

        headers = header(month_data, mean)
        rank_ordered_data = warp.order_by_rank(month_data)
        joined_data = month_data.reset_index(drop=True).join(
            rank_ordered_data.reset_index(drop=True)
        )
        write_output_xlsx(writer, headers, joined_data)

    writer = util.add_documentation_sheet(writer, util.documentation_file(output_filename()))

    writer.save()
    log.info('monthly_with_statistics created: %s', output_file)


if __name__ == '__main__':
    monthly_with_statistics()
