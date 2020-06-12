import calendar
import datetime as dt
import os

import click

import seaice.logging as seaicelogging
import seaice.timeseries as sit
import seaice.nasateam as nt

log = seaicelogging.init('seaice.tools')


@click.command()
@click.option('--output_directory',
              type=click.Path(exists=True, writable=True, resolve_path=True, file_okay=False),
              default='/share/apps/seaice/climatology_files/')
@click.option('--data_store', type=click.Path(exists=True, resolve_path=True, dir_okay=False),
              default=nt.DAILY_DATA_STORE_FILENAME)
@click.option('--start_year', type=click.INT, default=1981)
@click.option('--end_year', type=click.INT, default=2010)
@seaicelogging.log_command(log)
def sea_ice_climatology(output_directory, data_store, start_year, end_year):
    """Compile the normal_statistics and quantiles statistics from seaice.timeseries,
       and create a formatted output csv
    """
    log.info('Starting generation of climatology text files for {0} to {1}'.format(start_year,
                                                                                   end_year))

    # add buffer days for interpolation purposes
    start_date = dt.date(start_year, 1, 1) - dt.timedelta(1)
    end_date = dt.date(end_year, 12, 31) + dt.timedelta(1)

    # make sure end_year has a DOY 366
    if not calendar.isleap(end_year):
        end_date = end_date + dt.timedelta(1)

    quantiles = [.10, .25, .50, .75, .90]

    north_daily_extent_frame = sit.daily('N',
                                         start_date=start_date.isoformat(),
                                         end_date=end_date.isoformat(),
                                         data_store=data_store,
                                         interpolate=1)['total_extent_km2'] / 1e6
    south_daily_extent_frame = sit.daily('S',
                                         start_date=start_date.isoformat(),
                                         end_date=end_date.isoformat(),
                                         data_store=data_store,
                                         interpolate=1)['total_extent_km2'] / 1e6

    north_stats = sit.normal_statistics(north_daily_extent_frame, (start_year, end_year))
    south_stats = sit.normal_statistics(south_daily_extent_frame, (start_year, end_year))
    north_stats = north_stats.join(sit.quantiles(north_daily_extent_frame, levels=quantiles))
    south_stats = south_stats.join(sit.quantiles(south_daily_extent_frame, levels=quantiles))

    header = 'std Years = {}-{}\n'.format(start_year, end_year)
    north_file = 'N_seaice_extent_climatology_{}-{}_{}.csv'.format(start_year, end_year,
                                                                   nt.VERSION_STRING)
    south_file = 'S_seaice_extent_climatology_{}-{}_{}.csv'.format(start_year, end_year,
                                                                   nt.VERSION_STRING)
    north_subdir = _directory_subdir(output_directory, 'north')
    south_subdir = _directory_subdir(output_directory, 'south')

    _write_formatted_dataframe_to_csv(north_stats,
                                      os.path.join(north_subdir, north_file),
                                      quantiles, header)
    _write_formatted_dataframe_to_csv(south_stats,
                                      os.path.join(south_subdir, south_file),
                                      quantiles, header)


def _directory_subdir(root, hemi):
    """Create climatology subdir structure, and ensure it exists."""
    subdir = os.path.join(root, hemi, 'daily', 'data')
    os.makedirs(subdir, exist_ok=True)
    return subdir


def _write_formatted_dataframe_to_csv(df_in, out_file, quantiles, header):
    margin = ' ' * 3
    precision = 3

    df = df_in.copy()
    df = df[['total_extent_km2_mean', 'total_extent_km2_std'] + quantiles]

    # Move DOY into columns and rename columns
    df.reset_index(level=0, inplace=True)
    df.columns = (['DOY', 'Average Extent', 'Std Deviation'] +
                  [' ' * precision + '{0:g}'.format(100*x) + 'th' for x in quantiles])

    # Round values to 3 decimal places
    df = df.round(precision)

    # Pad DOY column
    df['DOY'] = df['DOY'].apply(lambda x: '{:>03d}'.format(x))

    # Set all data columns to be "column label width + float formatted to precision"
    for column in df.columns[1:]:
        df[column] = df[column].apply(
            lambda x: margin + '{{:{}.{}f}}'.format(len(column), precision).format(x))

    # Add margin spacing to column headers
    df.columns = ['DOY'] + [margin + x for x in df.columns[1:]]

    output = header + df.to_csv(index=False)
    with open(out_file,  'w') as text_file:
        text_file.write(output)

    log.info('Wrote climatology csv to {}'.format(out_file))


if __name__ == '__main__':
    sea_ice_climatology()
