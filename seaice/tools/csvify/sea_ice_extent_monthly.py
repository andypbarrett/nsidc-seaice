import os

import click

import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit
from .. import warp

log = seaicelogging.init('seaice.tools')


@click.command()
@click.argument('input_directory', type=click.Path(exists=True, file_okay=False),
                default=nt.DATA_STORE_BASE_DIRECTORY)
@click.argument('out_dir', type=click.Path(exists=True, file_okay=False),
                default=None)
@seaicelogging.log_command(log)
def sea_ice_extent_monthly(input_directory, out_dir):
    """Take the monthly extent and missing stats for every month from the sedna
    output, and create a more human-readable CSV for the G02135 dataset.

    """
    input_file = os.path.join(input_directory, 'monthly.p')

    north_df = sit.monthly('N', data_store=input_file)
    south_df = sit.monthly('S', data_store=input_file)

    north_df = warp.seaicetimeseries_df_to_monthly_csv_df(north_df)
    south_df = warp.seaicetimeseries_df_to_monthly_csv_df(south_df)

    month_list = list(range(1, 12 + 1))
    north_monthly_dfs = warp.split_by_column(north_df, 'mo', values=month_list)
    south_monthly_dfs = warp.split_by_column(south_df, 'mo', values=month_list)

    for index, df_ in enumerate(north_monthly_dfs):
        month = index + 1
        _write_monthly_csv_file(df_, month, 'north', out_dir)

    for index, df_ in enumerate(south_monthly_dfs):
        month = index + 1
        _write_monthly_csv_file(df_, month, 'south', out_dir)


def _df_data_str(df_in):
    """Reorder/rename columns appropriately, add whitespace to data values and
    column headers.

    """
    df = df_in.copy()
    df = df.rename(columns={'hemisphere': 'region'})

    df = df[['year', 'mo', 'data-type', 'region', 'extent', 'area']]
    df = warp.float_columns_to_string(df, ['extent', 'area'], 2)

    df = warp.columns_to_width(df, {
        'mo': 3,
        'data-type': 13,
        'region': 7,
        'extent': 7,
        'area': 7
    })

    return df.to_csv(index=False)


def _write_monthly_csv_file(df_in, month, hemisphere,
                            out_dir=None):
    df = df_in.copy()

    if len(df) == 0:
        return

    month_number = int(month)
    text = _df_data_str(df)

    if out_dir is None:
        out_dir = os.path.join(nt.SEA_ICE_BASE_DIR, 'csv', hemisphere, 'monthly', 'data')

    filename = '{hemi}_{month:02d}_extent_{ver}.csv'.format(hemi=hemisphere.capitalize()[0],
                                                            month=month_number,
                                                            ver=nt.VERSION_STRING)
    full_out_dir = os.path.join(out_dir, hemisphere, 'monthly', 'data')
    full_filename = os.path.realpath(os.path.join(full_out_dir, filename))

    if not os.path.isdir(full_out_dir):
        os.makedirs(full_out_dir)

    with open(full_filename, 'w') as txt_file:
        txt_file.write(text)
        log.info('sea_ice_monthly created: %s', full_filename)


if __name__ == '__main__':
    sea_ice_extent_monthly()
