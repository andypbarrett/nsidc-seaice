import os
import io
import re

import click
import pandas as pd

import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit

from .. import warp

log = seaicelogging.init('seaice.tools')


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False),
                default=nt.DATA_STORE_BASE_DIRECTORY)
@click.argument('output_directory', type=click.Path(exists=True, file_okay=False),
                default=None)
@seaicelogging.log_command(log)
def sea_ice_extent_daily(input_directory, output_directory):
    """Take the daily extent and missing stats for every day from the sedna output,
    and create a more human-readable CSV for the G02135 dataset.

    """
    input_file = os.path.join(input_directory, 'daily.p')

    north_df = sit.daily('N', data_store=input_file)
    south_df = sit.daily('S', data_store=input_file)
    north_df = warp.seaicetimeseries_df_to_extent_csv_df(north_df)
    south_df = warp.seaicetimeseries_df_to_extent_csv_df(south_df)
    north_df = warp.change_filepaths_to_ftp(north_df)
    south_df = warp.change_filepaths_to_ftp(south_df)

    _write_df_to_csv(north_df, 'north', output_directory)
    _write_df_to_csv(south_df, 'south', output_directory)


def _add_description_row(df_in):
    """Return a new copy of the given dataframe with a new row containing
    descriptions for the format of values in each column.

    """

    df = pd.DataFrame(columns=df_in.columns)

    source_desc = (' Source data product web sites: http://nsidc.org/data/nsidc-0081.html and '
                   'http://nsidc.org/data/nsidc-0051.html')

    df.loc[0] = ['YYYY',
                 '    MM',
                 '  DD',
                 ' 10^6 sq km',
                 ' 10^6 sq km',
                 source_desc]
    df = df.append(df_in)

    return df


def _write_df_to_csv(df_in, hemisphere, out_dir=None):
    """Write the given dataframe to a seaice_extent.csv file under the given
    out_dir. Kind and hemisphere must be specified to determine the name of the
    file to be written, and to give the file the correct description row (under
    the header and above the data).

    """
    df = df_in.copy()

    if len(df) == 0:
        return

    # reorder and rename columns
    df = df[['year', 'month', 'day', 'extent', 'missing', 'filename']]
    df.columns = ['Year', 'Month', 'Day', 'Extent', 'Missing', 'Source Data']

    # reformat values with proper whitespace, precision, and leading zeros
    df.Month = df.Month.apply(lambda x: '{:>6}'.format(str(x).zfill(2)))
    df.Day = df.Day.apply(lambda x: '{:>4}'.format(str(x).zfill(2)))
    df.Extent = df.Extent.apply(lambda x: '{:>11.3f}'.format(x))
    df.Missing = df.Missing.apply(lambda x: '{:>11.3f}'.format(x))
    df['Source Data'] = df['Source Data'].apply(lambda x: ' {}'.format(x))

    # reformat column headers with proper whitespace
    df.columns = ['Year',
                  '{:>6}'.format('Month'),
                  '{:>4}'.format('Day'),
                  '{:>11}'.format('Extent'),
                  '{:>11}'.format('Missing'),
                  ' Source Data']

    df = _add_description_row(df)

    if out_dir is None:
        out_dir = os.path.join(nt.SEA_ICE_BASE_DIR, 'csv', hemisphere, 'daily', 'data')

    filename = '{hemi}_seaice_extent_daily_{ver}.csv'.format(hemi=hemisphere[0].capitalize(),
                                                             ver=nt.VERSION_STRING)
    full_out_dir = os.path.join(out_dir, hemisphere, 'daily', 'data')
    full_filename = os.path.realpath(os.path.join(full_out_dir, filename))

    if not os.path.isdir(full_out_dir):
        os.makedirs(full_out_dir)

    output = open(full_filename, 'w')
    output.write(_reformat_source_data_list(df))
    output.close()

    log.info('sea_ice_extent_csvs created: %s', full_filename)


def _reformat_source_data_list(df):
    '''Change '," [list, goes, here] "' to ' "[list, goes, here] "
       for user readability reasons'''
    csv = io.StringIO()
    df.to_csv(csv, index=False)
    csv = csv.getvalue()
    return re.sub('," ', ',"', csv)


if __name__ == '__main__':
    sea_ice_extent_daily()
