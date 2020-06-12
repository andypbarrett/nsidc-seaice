#!/usr/bin/env python

"""Creates monthly_ice_anomaly_{month}_{hemi}.png images from data obtained with
the seaicetimeseries package using plotly.

"""
import calendar as cal
import math
import os

import click
import numpy as np
import plotly.graph_objs as go
import scipy.stats

from seaice.tools.plotter.util import save_plot
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')


def figure_monthly_anomaly(df_in, hemi, month):
    """Return a plotly Figure object which can be drawn interactively in a jupyter
    notebook with plotly.offline.iplot, or saved to a file with
    plotly.plotly.image.save_as.

    Arguments
    ---------

    df_in: the data to graph. The index is a PeriodIndex with
        frequency='M'. Columns are ['extent', 'anomaly', and
        'anomaly_trend'].

    hemi: 'N' or 'S'

    month: int representing the month to plot

    """
    df = df_in.copy()

    # plotly figure-wide settings
    layout = _get_layout(df, hemi, month)

    # plotly scatter plots
    data = _get_scatter_plots(df)

    return go.Figure({'data': data, 'layout': layout})


def df_monthly_anomaly(data_store, hemi, month):
    """Return a pandas DataFrame with all the info we need to create the anomaly
    percentage plot. The columns in the returned dataframe are: extent (in
    millions of km^2), anomaly, and anomaly_trend. The extent column is needed
    to create the annotation for the graph that gives the mean extent.

    Arguments
    ---------
    data_store: path to CSV file containing monthly extents

    hemi: 'N' or 'S'

    month: int representing the month to plot

    """
    df = sit.monthly(hemisphere=hemi, data_store=data_store, month_num=month)

    # scale to millions of sq km
    df['extent'] = df.total_extent_km2 / 1e6

    # percentage difference between the climatological mean and the extent for a
    # given month
    df['anomaly'] = sit.monthly_percent_anomaly(df.extent, nt.DEFAULT_CLIMATOLOGY_YEARS)

    # trendline for anomaly
    df['anomaly_trend'] = sit.trend(df.anomaly)

    df = df[['extent', 'anomaly', 'anomaly_trend']]

    return df


def _get_scatter_plots(df_in):
    """Return list of plotly Scatter objects, i.e., return the lines to graph for
    the extent anomaly and trend.

    Arguments
    ---------
    df_in: pandas DataFrame with a monthly PeriodIndex and columns ['anomaly',
        'anomaly_trend'].

    """
    df = df_in.copy()

    anomalies = go.Scatter(
        name='Extent Anomaly',
        x=df.index.year,
        y=df.anomaly,
        connectgaps=True,
        mode='lines+markers',
        line=dict(
            color='black',
            width=1.5
        ),
        marker=dict(
            symbol='cross',
            color='black'
        )
    )

    trend = go.Scatter(
        name='Best Fit Line',
        x=df.index.year,
        y=df.anomaly_trend,
        line=dict(
            color='grey',
            dash='7',
            width=1
        )
    )

    return [anomalies, trend]


def _round_to_nearest_multiple_up(x, n=5):
    """Round up from x to the nearest multiple of n."""
    return n * math.ceil(float(x) / n)


def _round_to_nearest_multiple_down(x, n=5):
    """Round down from x to the nearest multiple of n."""
    return n * math.floor(float(x) / n)


def _y_range(series, interval_size=5, threshold=1):
    """Return a list containing two elements: the minimum and maximum values to draw
    on the y-axis of the anomaly graph. By default, we want to draw -25 to 25,
    but if any data in the given series is outside of that range, we need to
    increase the boundaries.

    Arguments
    ---------
    series: the data to plot on the y-axis; its min and max affect the returned
        boundaries

    interval_size: an int; the boundaries of the y-axis will be multiples of
        this number. For example, if the maximum value in the series is 37 and
        interval_size is 3, the upper bound of the graph will be 39.

    threshold: if the difference between the boundary of the range and a series
        extremum is less than the threshold, then the boundary is pushed out
        further an additional interval_size

    """

    # default bounds
    y_min = -25
    y_max = 25

    min_value = min(series)
    max_value = max(series)

    if min_value < y_min:
        y_min = _round_to_nearest_multiple_down(min_value, interval_size)
    if max_value > y_max:
        y_max = _round_to_nearest_multiple_up(max_value, interval_size)

    if -threshold <= (y_min - min_value) <= 0:
        y_min -= interval_size
    if 0 <= (y_max - max_value) <= threshold:
        y_max += interval_size

    return [y_min, y_max]


def _get_layout(df_in, hemi, month):
    """Return a plotly Layout object containing styling information which applies to
    the whole graph.

    df_in: pandas DataFrame with a monthly PeriodIndex and columns ['extent',
        'anomaly'].

    hemi: 'N' or 'S'

    month: int representing the month to plot

    """

    df = df_in.copy()

    start_year = min(df.index.year)
    end_year = max(df.index.year)

    return go.Layout(dict(
        title='{hemisphere} Hemisphere Extent Anomalies {month_name} {start} - {end}'.format(
            hemisphere={'N': 'Northern', 'S': 'Southern'}[hemi],
            month_name=cal.month_abbr[month],
            start=start_year,
            end=end_year
        ),

        xaxis=dict(
            title='slope = {} per decade'.format(_slope_string(df)),
            range=[start_year - 1, end_year + 1],
            showline=True,
            tick0=nt.DEFAULT_CLIMATOLOGY_YEARS[0] - 1,
            dtick=5
        ),
        yaxis=dict(
            title='%',
            range=_y_range(df.anomaly),
            showline=True,
            zeroline=False
        ),

        font=dict(
            color='#000000'
        ),

        showlegend=False,

        width=630,
        height=360,

        annotations=[
            dict(
                text=_mean_string(df.extent, month),
                xref='paper',
                yref='paper',
                x=0,
                y=0,
                showarrow=False
            ),
            dict(
                text='National Snow and Ice Data Center, University of Colorado, Boulder',
                xref='paper',
                yref='paper',
                x=1.08,
                y=-.15,
                textangle=270,
                showarrow=False,
                font=dict(
                    size=9
                )
            )
        ]
    ))


def _mean_string(series, month, years=nt.DEFAULT_CLIMATOLOGY_YEARS):
    """Return string describing the mean value of the data contained in the given
    series in the given month, across the specified years.

    """
    start, end = years
    mean = sit.climatology_means(series, (start, end)).loc[month]

    return '{start}-{end} mean = {mean:.1f} million sq km'.format(start=start,
                                                                  end=end,
                                                                  mean=mean)


def _slope_string(df_in):
    """Return string describing the change in extent per decade with respect to the
    climatological mean.

    df_in: pandas DataFrame with a monthly PeriodIndex and column 'anomaly'

    """
    df = df_in.copy()

    x = df.index.year
    y = np.ma.masked_invalid(df.anomaly)

    if y.mask.any():
        mask = y.mask
        x = x[~mask]
        y = y[~mask]

    slope, _, _, _, std_err = scipy.stats.linregress(x, y)
    uncertainty = scipy.stats.t.interval(0.95, len(x) - 2)[1] * std_err

    # scale by decade
    slope *= 10
    uncertainty *= 10

    plus_minus = '±'

    return '{slope:.1f} {symbol} {uncertainty:.1f} %'.format(
        slope=slope,
        uncertainty=uncertainty,
        symbol=plus_minus
    )


def _directory_subdir(hemi, month_num):
    """ The subdirectory structure for the given hemi and month."""
    month_dir = '{:02}_{}'.format(month_num, cal.month_abbr[month_num])
    return os.path.join(nt.by_name(hemi)['long_name'],
                        'monthly', month_dir)


@click.command()
@click.argument('data_store', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_dir', type=click.Path(exists=True, file_okay=False))
@click.option('-h', '--hemi',
              type=click.Choice(['N', 'S']), default='none')
@click.option('-m', '--month', type=int)
@click.option('-v', '--version-string', default=nt.VERSION_STRING,
              help=('Version string for output files.'))
@click.option('--hires', type=bool, is_flag=True, default=False,
              help=('Create a higher resolution version of the plot image.'))
@seaicelogging.log_command(log)
def monthly_anomaly(data_store, output_dir, hemi, month, version_string, hires):
    """Create a plotly graph showing monthly anomalies using monthly data from
    data_store for the given hemi and month, saved to a .png in output_dir.

    """

    resolution_id = 'hires_' if hires else ''
    scale = 2. if hires else 2/3.

    filename = '{hemi}_{month:02}_extent_anomaly_plot_{resolution}{version}.png'.format(
        month=month, hemi=hemi, resolution=resolution_id, version=version_string)

    output_dir = os.path.join(output_dir,  _directory_subdir(hemi, month))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)

    df = df_monthly_anomaly(data_store, hemi, month)
    figure = figure_monthly_anomaly(df, hemi, month)

    save_plot('monthy_anomaly', figure, output_file, scale=scale)


if __name__ == '__main__':
    monthly_anomaly()
