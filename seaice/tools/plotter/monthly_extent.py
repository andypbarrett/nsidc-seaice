#!/usr/bin/env python

"""Creates monthly_ice_{month}_{hemi}.png images (ASINA Figure 3) from data
obtained with the seaicetimeseries package using plotly.

"""
import calendar
import math
import os

import click
import numpy as np
import plotly.graph_objs as go

from seaice.tools.plotter.util import save_plot
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')


def figure_monthly_extent(df_in, hemi, month):
    """Return a plotly Figure object which can be drawn interactively in a jupyter
    notebook with plotly.offline.iplot, or saved to a file with
    plotly.plotly.image.save_as.

    Arguments
    ---------

    df_in: the data to graph. The index is a PeriodIndex with
        frequency='M'. Columns are ['year', 'extent', and
        'extent_trend'].

    hemi: 'N' or 'S'

    month: int representing the month to plot

    """
    df = df_in.copy()

    # plotly figure-wide settings
    layout = _get_layout(df, hemi, month)

    # plotly scatter plots
    data = _get_data(df)

    return go.Figure({'data': data, 'layout': layout})


def df_monthly_extent(data_store, hemi, month):
    df = sit.monthly(hemisphere=hemi, data_store=data_store, month_num=month)

    # scale and pick the columns we care about
    df['year'] = df.index.year
    df['extent'] = df.total_extent_km2 / 1e6
    df = df[['year', 'extent']]

    # trendline for extent in millions of km^2
    df['extent_trend'] = sit.trend(df.extent)

    return df


def _missing_boundaries(series):
    """Returns a list of pairs of indices. Each pair of indices in the returned list
    is an index in the given series with valid data, where all of the data in
    between those two is missing (NaN). These indices with valid data can be
    used to draw lines to cover the missing sections of plots.

    """
    pairs = []

    clumps = np.ma.clump_masked(np.ma.masked_invalid(series))

    for clump in clumps:
        # ignore missing clumps at start or end of the data since we need a
        # valid point on both sides of the clump to draw the missing line
        if (clump.start == 0) or (clump.stop == len(series)):
            continue

        pairs.append([clump.start - 1, clump.stop])

    return pairs


def _get_data(df_in):
    """Returns a plotly Data object containing the Scatter objects for the extent
    and extent_trend columns in df_in, as well as Scatter objects to fill in any
    missing sections with a dashed line.

    """
    df = df_in.copy()

    extents = go.Scatter(
        x=df.year,
        y=df.extent,
        name='Extent',
        showlegend=False,
        line={
            'color': 'black'
        }
    )

    trend = go.Scatter(
        x=df.year,
        y=df.extent_trend,
        name='Best Fit Line',
        showlegend=False,
        line={
            'color': 'blue'
        }
    )

    missing = []
    for boundaries in _missing_boundaries(df.extent):
        scatter_plot = go.Scatter(
            x=df.year[boundaries],
            y=df.extent[boundaries],
            name='Missing Extent',
            mode='lines',
            line={
                'color': 'black',
                'dash': 'dot'
            }
        )
        missing.append(scatter_plot)

    return go.Data([extents, trend] + missing)


def _get_layout(df_in, hemi, month):
    """Returns a plotly Layout object containing styling information which applies
    to the whole graph.

    """
    df = df_in.copy()

    return go.Layout({
        'title': 'Average Monthly {region} Sea Ice Extent<br>{month_name} {start} - {end}'.format(
            region={'N': 'Arctic', 'S': 'Antarctic'}[hemi],
            month_name=calendar.month_name[month],
            start=min(df.year),
            end=max(df.year)
        ),

        'xaxis': {
            'title': 'Year',
            'range': [min(df.year) - 1, max(df.year) + 1],
            'showline': True,
            'dtick': 4
        },
        'yaxis': {
            'title': 'Extent (millions of square kilometers)',
            'range': [math.floor(min(df.extent)), math.ceil(max(df.extent))],
            'showline': True,
        },

        'font': {
            'color': '#000000'
        },

        'legend': {
            'xanchor': 'right'
        },

        # default is 700x500, but that is not quite the same aspect ratio as the
        # old monthly extent images
        'width': 660,
        'height': 510,

        'annotations': [
            {
                'text': 'National Snow and Ice Data Center',
                'showarrow': False,
                'textangle': 270,
                'xref': 'paper',
                'yref': 'paper',
                'x': 1.05,
                'y': 0
            }
        ]
    })


@click.command()
@click.argument('data_store', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_dir', type=click.Path(exists=True, file_okay=False))
@click.option('-h', '--hemi',
              type=click.Choice(['N', 'S']), default='none')
@click.option('-m', '--month', type=int)
@click.option('--version-string', type=str, default=nt.VERSION_STRING)
@seaicelogging.log_command(log)
def monthly_extent(data_store, output_dir, hemi, month, version_string):
    """Create a plotly graph showing monthly extent using monthly data from
    data_store for the given hemi and month, saved to a .png in output_dir.

    """

    filename = 'monthly_ice_{month:02}_{hemi}H_{version_string}.png'.format(
        month=month,
        hemi=hemi,
        version_string=version_string
    )

    output_file = os.path.join(output_dir, filename)

    df = df_monthly_extent(data_store, hemi, month)
    figure = figure_monthly_extent(df, hemi, month)

    save_plot('monthly_extent', figure, output_file, scale=2)


if __name__ == '__main__':
    monthly_extent()
