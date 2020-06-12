import calendar as cal
from collections import Counter
import copy
import datetime as dt
from dateutil.relativedelta import relativedelta
import math
import operator
import os
import re
import subprocess

import click
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import yaml

from seaice.tools.errors import SeaIceToolsError
from seaice.tools.errors import SeaIceToolsRuntimeError
from seaice.tools.errors import SeaIceToolsValueError
from seaice.tools.plotter.util import save_plot
import seaice.nasateam as nt
import seaice.logging as seaicelogging
import seaice.timeseries as sit


log = seaicelogging.init('seaice.tools')

DEFAULTS = {
    'date': dt.date.today(),
    'plot_mean': False,
    'plot_stdev': False,
    'plot_median': False,
    'plot_iqr': False,
    'plot_idr': False,
    'hemi': None,
    'month_bounds': (-3, 1),
    'nstdevs': 2,
    'percentiles': [],
    'styles': [],
    'year_styles': {},
    'years': [],
    'data_store': nt.DAILY_DATA_STORE_FILENAME,
    'output_dir': None,
    'output_file': 'daily_ice_extent_{hemi}.png',
    'nday_average': 5,
    'divisor': 1e6,
    'min_valid': 2,
    'legend_side': None
}

PERCENTILE_COLUMN_REGEX = re.compile('^percentile_(?P<percent>.+)$')
YEAR_COLUMN_REGEX = re.compile('^\d{4}(?:-\d{4})?$')


def df_daily_extent(hemi, date=DEFAULTS['date'], years=DEFAULTS['years'],
                    month_bounds=DEFAULTS['month_bounds'], nstdevs=DEFAULTS['nstdevs'],
                    data_store=DEFAULTS['data_store'], nday_average=DEFAULTS['nday_average'],
                    percentiles=DEFAULTS['percentiles'], min_valid=DEFAULTS['min_valid'],
                    divisor=DEFAULTS['divisor']):
    """Returns a pandas DataFrame with all of the data to graph for the given date,
    and other years for comparison. The index is an integer index representing
    days since the first of the first month, e.g., with a date in March and a
    month_bounds of (-3, 1), index 0 contains values from December 1 of the
    preceding year.

    See the Click documentation on main() for argument information.

    """
    # default to 5 months, with the target date falling in the 4th
    start_date, end_date = _bounding_date_range(date, *month_bounds)
    date_index = pd.date_range(start_date, end_date, freq='D')

    # data for mean and stdev aligned to the date_index
    extents = sit.daily(hemi, interpolate=1)['total_extent_km2']
    df = _climatology_statistics(extents, date_index, nstdevs, percentiles, nday_average, divisor)

    df['date'] = date_index

    # uniquify and sort list of years
    years = np.unique(list(years) + [date.year])

    # drop any years after 'date'
    years = years[years <= date.year]

    # get the data for each year
    for year in years:
        new_index = _shift_index_to_year(date_index, date, year)
        data_year = _df_year(hemi, new_index, data_store, nday_average=nday_average,
                             min_valid=min_valid, divisor=divisor)
        df = df.merge(data_year, left_index=True, right_index=True, how='outer')

    # eliminate any data after the given date, to cut off the line
    rows = df.date > date
    col = _line_name(date_index)
    df.loc[rows, col] = np.nan

    return df


def figure(df_in, hemi, date=DEFAULTS['date'], plot_mean=DEFAULTS['plot_mean'],
           plot_stdev=DEFAULTS['plot_stdev'], styles=DEFAULTS['styles'],
           nstdevs=DEFAULTS['nstdevs'], plot_median=DEFAULTS['plot_median'],
           plot_iqr=DEFAULTS['plot_iqr'], plot_idr=DEFAULTS['plot_idr'],
           divisor=DEFAULTS['divisor'], legend_side=DEFAULTS['legend_side']):
    """Create a plotly Figure object from a pandas DataFrame containing columns for
    each line to plot, focused on the given date.

    See the Click documentation on main() for information on the arguments not
    listed below.

    Arguments
    ---------
    df_in: pandas DataFrame with an index starting at 0, representing days since
        the first of the first month shown on the graph.

    styles: a list of dicts that can be used for the 'line' value in a plotly
        Scatter object. These can be used to customize the plotly properties
        color, smoothing, dash, width, and shape.

    """
    df = df_in.copy()
    df = df.reset_index(drop=True)

    data_list = []

    # stdev region
    if plot_stdev:
        s = '' if nstdevs is 1 else 's'
        name = '± {n} Standard Deviation{s}'.format(n=nstdevs, s=s)

        plots_stdev = _scatter_plots_envelope(df.climatology_lower, df.climatology_upper, name)
        data_list.extend(plots_stdev)

    # climatology mean line
    if plot_mean:
        name = '1981-2010 Average'
        plot_mean = _scatter_plot_average(df.climatology, name)
        data_list.append(plot_mean)

    # interdecile region
    if plot_idr:
        name = 'Interdecile Range'
        plots_idr = _scatter_plots_envelope(df['percentile_10'], df['percentile_90'],
                                            name, fillcolor='rgba(229, 229, 229, 1)')
        data_list.extend(plots_idr)

    # interquartile region
    if plot_iqr:
        name = 'Interquartile Range'
        plots_iqr = _scatter_plots_envelope(df['percentile_25'], df['percentile_75'],
                                            name, fillcolor='rgba(206, 206, 206, 1)')
        data_list.extend(plots_iqr)

    # climatology median line
    if plot_median:
        name = '1981-2010 Median'
        plot_median = _scatter_plot_average(df['percentile_50'], name)
        data_list.append(plot_median)

    # lines for all the years
    plots_years = []
    year_styles = copy.deepcopy(styles)
    year_columns = [col for col in df.columns if re.match(YEAR_COLUMN_REGEX, col)]
    for year in year_columns:
        data_year = df[year]

        try:
            line_style = year_styles.pop(0)
        except IndexError:
            line_style = {}
        plot_year = _scatter_plot_year(data_year, line_style=line_style)

        plots_years.append(plot_year)

    data_list.extend(plots_years)

    layout = _layout(df, hemi, date, divisor, legend_side)

    return go.Figure({'data': data_list, 'layout': layout})


def _month_ticks_and_annotations(dates):

    month_nums = pd.Series(pd.to_datetime(dates.values).month)

    annotations = []
    tickvalues = []

    for thing in month_nums.groupby(month_nums):
        short_name = cal.month_abbr[thing[0]]
        days = thing[1].index
        day = days[int(len(days) / 2) - 1]

        # name of the month
        annotations.append({
            'text': short_name,
            'x': day,
            'showarrow': False,
            'yref': 'paper',
            'yanchor': 'bottom',
            'y': -.05,
            'font': {
                'size': 22
            }})

        # tick mark at the first of the month
        tickvalues.append(days[0])

    return tickvalues, annotations


def _y_range(df_in, hemi, min_range=10):
    """Return a list of length 2, containing a minimum and maximum value for the
    y-axis. All columns in df_in must be columns that will be plotted.

    """
    df = df_in.copy()

    y_min = math.floor(df.min(axis=1).min())
    y_max = math.ceil(df.max(axis=1).max())

    if (y_max - y_min) < min_range:
        y_min = y_max - min_range

    y_min = max(y_min - 1, 0)

    return [y_min, y_max]


def _y_axis_title(divisor=DEFAULTS['divisor']):
    descriptor = {
        1e7: 'tens of millions of ',
        1e6: 'millions of ',
        1e5: 'hundreds of thousands of ',
        1e4: 'tens of thousands of ',
        1e3: 'thousands of ',
        1e2: 'hundreds of ',
        1e1: 'tens of ',
        1e0: ''
    }.get(divisor, 'x{} '.format(divisor))

    title = 'Extent ({}square kilometers)'.format(descriptor)

    return title


def _layout(df_in, hemi, date=DEFAULTS['date'], divisor=DEFAULTS['divisor'],
            legend_side=DEFAULTS['legend_side']):
    df = df_in.copy()
    dates = df.date
    start_of_months, month_annotations = _month_ticks_and_annotations(dates)

    return {
        'font': {
            'color': 'rgba(0, 0, 0, 1)'
        },
        'margin': {
            't': 126,
            'r': 110,
            'b': 84,
            'l': 100
        },
        'xaxis': {
            'showline': True,
            'tickvals': start_of_months,
            'ticks': 'inside',
            'showticklabels': False,
            'zeroline': False
        },
        'yaxis': {
            'title': _y_axis_title(divisor),
            'showline': True,
            'titlefont': {
                'size': 28,
            },
            'range': _y_range(df, hemi),
            'tickfont': {
                'size': 22
            }
        },

        'title': ('{region} Sea Ice Extent<br>(Area of ocean with at least 15% sea ice)').format(
            region={'N': 'Arctic', 'S': 'Antarctic'}[hemi]
        ),
        'titlefont': {
            'size': 35
        },

        'width': 1050,
        'height': 840,

        'annotations': month_annotations + [
            {
                'text': 'National Snow and Ice Data Center, University of Colorado Boulder',
                'showarrow': False,
                'textangle': 270,
                'xref': 'paper',
                'yref': 'paper',
                'x': 1.03,
                'y': 0,
                'font': {
                    'size': 16
                }
            },
            {
                'text': date.strftime('%d %b %Y'),
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 1,
                'y': -.08,
                'font': {
                    'size': 14
                }
            }
        ],

        'showlegend': True,

        'legend': _legend(df, legend_side)
    }


def _legend(df_in, legend_side=DEFAULTS['legend_side']):
    df = df_in.copy().drop('date', axis=1)

    if legend_side == 'left':
        xanchor = 'left'
        x = 0

    elif legend_side == 'right':
        xanchor = 'right'
        x = 1

    else:
        max_idx = df['climatology'].idxmax()
        min_idx = df['climatology'].idxmin()

        is_concave_up = (max_idx == 0) or (max_idx == (len(df) - 1))

        local_extreme = min_idx if is_concave_up else max_idx
        is_local_extreme_on_left = local_extreme < (len(df) / 2)

        use_left_side = operator.xor(is_concave_up, is_local_extreme_on_left)

        if use_left_side:
            xanchor = 'left'
            x = 0
        else:
            xanchor = 'right'
            x = 1

    return {
            'xanchor': xanchor,
            'yanchor': 'bottom',
            'x': x,
            'y': 0,
            'bgcolor': 'rgba(0, 0, 0, 0)',
            'font': {
                    'size': 22
                }
        }


def _shift_index_to_year(dt_index, target_date, new_year):
    """Return new datetime index for the new_year

    given a dt_index we can shift it a number of years relative to the
    target_date and new_year returning a datetime index aligned with the initial
    dt_index, but for the target_year

    """
    if target_date not in dt_index:
        msg = 'Invalid target date {date}. Must be present in datetime index ({index})'.format(
            date=target_date,
            index=dt_index
        )
        raise SeaIceToolsRuntimeError(msg)

    shifted_index_start = dt_index[0]
    delta_years = target_date.year - new_year
    shifted_index_start = shifted_index_start - pd.DateOffset(years=delta_years)
    shifted_index = pd.date_range(start=shifted_index_start, periods=len(dt_index), freq='D')
    return shifted_index


def _df_year(hemi, date_index=None,
             data_store=DEFAULTS['data_store'], interpolate=1,
             nday_average=DEFAULTS['nday_average'], min_valid=DEFAULTS['min_valid'],
             divisor=DEFAULTS['divisor']):

    daily = sit.daily(hemi, data_store=data_store, interpolate=interpolate,
                      nday_average=nday_average, min_valid=min_valid)
    daily.index = pd.to_datetime(daily.index)

    df = pd.DataFrame()

    df['extent'] = daily.total_extent_km2 / divisor

    df = df.reindex(date_index)

    df.index = df.index.dayofyear

    df = df.rename(columns={'extent': _line_name(date_index)})
    df = df.reset_index(drop=True)

    return df


def _bounding_date_range(date, first_month_offset, last_month_offset):
    first_of_first_month = (date + relativedelta(months=first_month_offset)).replace(day=1)
    last_of_last_month = (
        (date + relativedelta(months=last_month_offset+1)).replace(day=1) - relativedelta(days=1)
    )
    return (first_of_first_month, last_of_last_month)


def _date_index_prepend_days(dt_index, days):
    """return a new extended datetime index.

    The input index is extended by 'days' at beginning of input dt_index

    """
    prepend_index = pd.date_range(dt_index[0] - dt.timedelta(days), dt_index[0])
    return dt_index.union(prepend_index)


def _climatology_statistics(extents, date_index, nstdevs=DEFAULTS['nstdevs'],
                            percentiles=DEFAULTS['percentiles'],
                            nday_average=DEFAULTS['nday_average'], divisor=DEFAULTS['divisor']):

    """Returns a smoothed dataframe indexed by the day of year for the input
    datetime_index, which describes the range that will be graphed.

    """

    mean_stddev = sit.normal_statistics(extents)
    mean_stddev_doy = _extend_smooth_divide(mean_stddev, date_index, nday_average, divisor)

    means = mean_stddev_doy.total_extent_km2_mean
    stds = mean_stddev_doy.total_extent_km2_std * nstdevs

    df = pd.DataFrame({
        'climatology': means,
        'climatology_upper': means + stds,
        'climatology_lower': means - stds
    })

    levels = [float(percentile) / 100 for percentile in percentiles]
    quantiles = sit.quantiles(extents, levels=sorted(levels))
    extent_processed = _extend_smooth_divide(quantiles, date_index, nday_average, divisor)

    for percentile, level in zip(percentiles, levels):
        df['percentile_{}'.format(percentile)] = extent_processed[level]

    df = df.reindex(date_index.dayofyear)
    df = df.reset_index(drop=True)
    return df


def _extend_smooth_divide(df, dt_index, nday_average, divisor):
    """Re-index, apply smoothing, apply divisor"""
    large_index = _date_index_prepend_days(dt_index, nday_average)
    large_df = df.reindex(large_index.dayofyear)
    smoothed_df = large_df.rolling(window=nday_average, min_periods=0).mean()
    return smoothed_df / divisor


def _line_name(date_index):
    start = date_index[0].year
    end = date_index[-1].year

    if start == end:
        return str(start)
    else:
        return '{start}-{end}'.format(start=start, end=end)


def _scatter_plot_year(series, line_style={}):
    line = {'width': 3}

    line.update(line_style)

    return go.Scatter(
        name=series.name,
        x=series.index,
        y=series.values,
        hoverinfo='y',
        line=line
    )


def _scatter_plot_average(series, name):
    return go.Scatter(
        name=name,
        x=series.index,
        y=list(series),
        hoverinfo='y',
        line={
            'color': 'rgba(150, 150, 150, 1)',
            'width': 3
        }
    )


def _scatter_plots_envelope(series_lower, series_upper, name, fillcolor='rgba(240, 240, 240, 1)'):
    kwargs = {
        'name': name,
        'line': {'color': 'rgba(0, 0, 0, 0)'},
        'hoverinfo': 'y'
    }

    upper = go.Scatter(
        x=series_upper.index,
        y=list(series_upper),
        showlegend=False,
        **kwargs
    )

    lower = go.Scatter(
        x=series_lower.index,
        y=list(series_lower),
        fillcolor=fillcolor,
        fill='tonexty',
        **kwargs
    )

    return [upper, lower]


def _config_from_file(configfile):
    """Return a dict containing all of the config values found in the given
    configfile.

    """

    conf = {}

    # set from config if possible
    if configfile:
        with open(configfile, 'r') as fp:
            config_yaml = yaml.load(fp)

        conf = config_yaml

        # in the config yaml, 'years' is a map of years to styles; in the config
        # dict used in this module, 'year_styles' is that map and 'years' is
        # simply a list of the years to graph
        conf['year_styles'] = conf.pop('years', {})
        conf['years'] = list(conf['year_styles'].keys())

    return conf


def _config_from_cli(cli_args):
    cli_config = dict((k, v) for k, v in cli_args.items() if v is not None)

    parse = {
        'date': lambda x: dt.datetime.strptime(x, '%Y-%m-%d').date(),
        'month_bounds': lambda x: [int(month) for month in x.split(',')][0:2],
        'percentiles': lambda x: [int(percentile) for percentile in x.split(',')][0:2],
        'years': lambda x: [int(year) for year in x.split(',')]
    }

    for key, parser in parse.items():
        if key in cli_config:
            cli_config[key] = parser(cli_config[key])

    return cli_config


def _validate_config(config):
    errors = []

    def error(msg):
        errors.append('Invalid configuration: {}.'.format(msg))

    if config['plot_mean'] and config['plot_median']:
        error('can only plot one of mean and median')

    # if config['plot_mean'] and config['plot_percentiles']:
    #     error('cannot plot percentiles with mean')

    if config['plot_median'] and config['plot_stdev']:
        error('cannot plot stdev with median')

    if config['plot_stdev'] and (config['plot_idr'] or config['plot_iqr']):
        error('can only plot one of stdev and percentiles')

    if config['hemi'] not in ['N', 'S']:
        error('hemi must be \'N\' or \'S\'')

    if config['nstdevs'] < 0:
        error('nstdevs cannot be negative')

    if config['nday_average'] < 0:
        error('nday_average cannot be negative')

    if not os.path.isfile(config['data_store']):
        error('data_store must exist')

    if config['min_valid'] > config['nday_average']:
        error('min_valid must be less than or equal to nday_average')

    if config['divisor'] <= 0:
        error('divisor must be positive')

    if errors:
        raise SeaIceToolsError('\n'.join(errors))


def _year_with_most_months_in_index(date_index):
    """
    Arguments
    ---------
    date_index: pandas DatetimeIndex. It is expected that every month contained
        in the index will have its first day in the index.
    """
    count = Counter(date_index[date_index.day == 1].year)
    years = [val for val, c in count.items() if c == max(count.values())]
    return min(years)


def _get_record_year(series, date, month_bounds, kind):
    """Get the year that should be plotted to represent the record minimum or
    maximum for the given series of data.

    The returned year may not be the year containing the actual record data
    point; graphs can be created with a year changeover, in which case a line
    represents multiple years; a single year is still used to generate that
    line.

    See the Click documentation on main() for information on the arguments not
    listed below.

    Arguments
    ---------
    series: pandas Series of the data to plot. Its index must be convert-able to
        a DatetimeIndex (i.e., with pd.to_datetime()).

    kind: a string describing what kind of record to get, and can be one of
        these values:
        * 'max': the year containing the date with the highest overall value in
                 the series
        * 'min': the year containing the date with the lowest overall value in
                 the series

    """
    series = series.copy()
    series.index = pd.to_datetime(series.index)

    start_date, end_date = _bounding_date_range(date, *month_bounds)
    date_index = pd.date_range(start_date, end_date, freq='D')

    extrema = {
        'max': 'idxmax',
        'min': 'idxmin',
    }[kind]

    if start_date.year - end_date.year > 1:
        raise SeaIceToolsValueError('Can\'t compute record year for more than 2 years.')

    single_year = start_date.year == end_date.year

    if single_year:
        cutoff_date = pd.to_datetime(dt.date(start_date.year, 1, 1))
    else:
        cutoff_date = pd.to_datetime(start_date)

    series = series[series.index < cutoff_date]

    record_date = getattr(series, extrema)()

    # easy case; no year change in plot, return the record year.
    if single_year:
        return record_date.year

    focus_before_year_switch = date.year == date_index[0].year
    focus_after_year_switch = date.year == date_index[-1].year

    record_after_year_switch = (record_date.month
                                in date_index[date_index.year == date_index[0].year].month)
    record_before_year_switch = (record_date.month
                                 in date_index[date_index.year == date_index[-1].year].month)

    both_after = focus_after_year_switch & record_before_year_switch
    both_before = focus_before_year_switch & record_after_year_switch

    if both_before or both_after:
        return record_date.year

    if focus_after_year_switch & record_after_year_switch:
        return record_date.year + 1

    if focus_before_year_switch & record_before_year_switch:
        return record_date.year - 1

    # If we get this far, the record's month is not shown directly on the plot.
    # Handle special case where record_date could have just happened in the previous year.
    if record_date.year == date_index[0].year:
        if focus_after_year_switch:
            return record_date.year
        if focus_before_year_switch:
            return record_date.year - 1

    most_plotted_year = _year_with_most_months_in_index(date_index)
    year = record_date.year + (date.year - most_plotted_year)
    return year


def _get_record_low_year(series, date, month_bounds):
    """Return the year containing the lowest single value in series, excluding the
    year of the focal date.

    See the Click documentation on main() for information on the arguments not
    listed below.

    Arguments
    ---------
    series: a pandas Series with an index that can be compared with a
        datetime.date, e.g., a PeriodIndex or DatetimeIndex.

    """

    return _get_record_year(series, date, month_bounds, 'min')


def _get_record_high_year(series, date, month_bounds):
    """Return the year containing the highest single value in series, excluding the
    year of the focal date.

    See the Click documentation on main() for information on the arguments not
    listed below.

    Arguments
    ---------
    series: a pandas Series with an index that can be compared with a
        datetime.date, e.g., a PeriodIndex or DatetimeIndex.

    """

    return _get_record_year(series, date, month_bounds, 'max')


def _handle_special_year_values(config_in):
    config = copy.deepcopy(config_in)

    df = sit.daily(hemisphere=config['hemi'],
                   data_store=config['data_store'],
                   interpolate=1,
                   nday_average=config['nday_average'],
                   min_valid=config['min_valid'])

    series = df.total_extent_km2

    date = config['date']
    month_bounds = config['month_bounds']

    special_vals = {
        'current': date.year,
        'record_low_year': _get_record_low_year(series, date, month_bounds),
        'record_high_year': _get_record_high_year(series, date, month_bounds)
    }

    max_years_before = date.year - nt.BEGINNING_OF_SATELLITE_ERA.year
    for delta in range(1, max_years_before + 1):
        special_vals['years_before_' + str(delta)] = date.year - delta

    # "rename" keys in year_styles dict
    for old, new in special_vals.items():
        if old in config['year_styles']:
            style_settings = config['year_styles'].pop(old)
            if new in config['year_styles']:
                config['year_styles'][new].update(style_settings)
            else:
                config['year_styles'][new] = style_settings

    # replace values in years list
    for index, year in enumerate(config['years']):
        if year in special_vals:
            config['years'][index] = special_vals[year]

    config['years'] = [int(year) for year in config['years']]

    return config


def _configs_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(this_dir, os.pardir, 'configs')
    return os.path.realpath(path)


def _handle_special_legend_settings(config_in):
    config = copy.deepcopy(config_in)

    if config['legend_side']:
        return config

    if 'legend' in config:
        month = config['date'].month
        if month in config['legend']:
            config['legend_side'] = config['legend'][month]['legend_side']

    return config


def _process_config(kwargs):
    # if using a standard_plot, treat it as a special case of using --configfile
    standard_plot = kwargs.pop('standard_plot', None)
    if standard_plot:
        configfile = os.path.join(_configs_dir(), standard_plot + '.yaml')
    else:
        configfile = kwargs.pop('configfile', None)

    cli_config = kwargs

    # base config
    config = DEFAULTS

    # add settings from yaml config file
    config.update(_config_from_file(configfile))

    # add settings from CLI options
    config.update(_config_from_cli(cli_config))

    config = _handle_special_legend_settings(config)

    # update year keys like "years_before_1" and "record_low_year"
    config = _handle_special_year_values(config)

    config['years'] = sorted(set(config['years']))

    # match years to draw with respective styling configuration in the yaml
    config['styles'] = [config['year_styles'].get(year, {}) for year in config['years']]

    if config['output_file'] == DEFAULTS['output_file']:
        config['output_file'] = DEFAULTS['output_file'].format(hemi=config['hemi'])

    if config['output_dir']:
        config['output_file'] = os.path.join(config['output_dir'], config['output_file'])

    config['percentiles'] = []
    if config['plot_median']:
        config['percentiles'].extend([50])
    if config['plot_iqr']:
        config['percentiles'].extend([25, 75])
    if config['plot_idr']:
        config['percentiles'].extend([10, 90])

    _validate_config(config)

    return config


@click.command()
@click.option('--standard_plot', type=click.Choice(['north', 'south',
                                                    'asina_north', 'asina_south',
                                                    'north_iqr', 'south_iqr',
                                                    'asina_north_iqr', 'asina_south_iqr']),
              help=('Use predefined settings to generate a standard timeseries image. Other '
                    'options will override the values set in the standard plot config. This option '
                    'overrides --configfile.'))
@click.option('-c', '--configfile', type=click.Path(exists=True, dir_okay=False),
              help=('YAML file containing settings for the graph. All of the flags described below '
                    'can be set in this YAML file. Values set with the CLI flags will override '
                    'values found in the configuration file. One important exception is that '
                    '--years are handled a bit differently; custom styling for each year can be '
                    'defined, and only can be defined in the yaml configuration. The setting for '
                    '--legend_side can also be customized by month in the yaml file. For example '
                    'configurations, the files used by --standard_plot can be found in {}. This '
                    'option is ignored if --standard_plot is used.'.format(_configs_dir())))
@click.option('--data_store', type=click.Path(exists=True, dir_okay=False),
              help=('daily.p file containing the data for daily sea ice extent. Defaults to '
                    'DAILY_DATA_STORE_FILENAME, from the nasateam package.'))
@click.option('-o', '--output_file', type=click.Path(exists=False, dir_okay=False),
              help=('File destination for the image. Defaults to \'daily_ice_extent_{hemi}.png\''))
@click.option('--output_dir', type=click.Path(exists=True, file_okay=False),
              help=('Directory in which to save the created image. If none is provided, the '
                    'current directory is used; alternatively, the full path can be given in '
                    '--output_file setting.'))
@click.option('-h', '--hemi', type=click.Choice(['N', 'S']), default=None,
              help=('The hemisphere to plot.'))
@click.option('-d', '--date',
              help=('YYYY-MM-DD. The focal point of the graph. Any data after this point is not '
                    'plotted. Defaults to today.'))
@click.option('-y', '--years',
              help=('List of comma-separated years to plot. In addition to integers, some special '
                    'values may also be used: current (the actual current year), years_before_N '
                    '(N must be an integer; that many years before the year defined by --date), '
                    'record_low_year (year containing the single day with the lowest extent '
                    'value), and record_high_year (year containing the single day with the highest '
                    'extent value). No years after --date will be plotted. Example using both '
                    'years and special values: --years=record_low_year,2013,years_before_1,2000'))
@click.option('-m', '--month_bounds',
              help=('How many months before and after the --date to show on the plot, separated by '
                    'a comma. Defaults to \'-3,1\'.'))
@click.option('-n', '--nday_average', type=int,
              help=('Smooth the data by using a trailing average of this many days when plotting '
                    'each data point. Defaults to 5.'))
@click.option('--min_valid', type=int,
              help=('When calculating the trailing average, there must be at least this many days '
                    'with valid data in order to use the average instead of NaN. In other words, '
                    'if we want a trailing average with 5 days, but 4 of those days have missing '
                    'data, there is only 1 valid day, so if --min_valid is greater than 1, the '
                    '"average" will be NaN. Defaults to 2.'))
@click.option('--divisor', type=int,
              help=('By default, the extent data found in the --data_store is in square '
                    'kilometers. Such large values are not the best to work with, so they can be '
                    'divided by the value given here. Defaults to 1e6, so that millions of square '
                    'kilometers are plotted by default.'))
@click.option('--plot_mean/--no-plot_mean', default=None,
              help=('Plot a line showing the mean values for each day in the climatological time '
                    'period.'))
@click.option('--plot_stdev/--no-plot_stdev', default=None,
              help=('Plot a shaded region representing data within --nstdevs standard deviations '
                    'of the climatology mean.'))
@click.option('--nstdevs', type=int,
              help=('Number of standard deviations to plot. Defaults to 2.'))
@click.option('--plot_median/--no-plot_median', default=None,
              help=('Plot a line showing the median values for each day in the climatological time '
                    'period.'))
@click.option('--plot_iqr/--no-plot_iqr', default=None,
              help=('Plot a shaded region representing data within the 25-75 percentile '
                    'range (interquartile range).'))
@click.option('--plot_idr/--no-plot_idr', default=None,
              help=('Plot a shaded region representing data within the 10-90 percentile '
                    'range (interdecile range).'))
@click.option('--legend_side', type=click.Choice(['left', 'right']), default=None,
              help=('Which side of the graph on which to plot the legend. By default, a side will '
                    'be chosen in a manner which attempts to prevent the legend from overlapping '
                    'with any of the data.'))
@seaicelogging.log_command(log)
def daily_extent(**kwargs):
    """Generate a graph showing daily sea ice extent over time.
    """

    config = _process_config(kwargs)

    # dataframe with columns for all the rows to plot
    df = df_daily_extent(config['hemi'],
                         date=config['date'],
                         years=config['years'],
                         month_bounds=config['month_bounds'],
                         nstdevs=config['nstdevs'],
                         data_store=config['data_store'],
                         nday_average=config['nday_average'],
                         percentiles=config['percentiles'],
                         min_valid=config['min_valid'],
                         divisor=config['divisor'])

    plot_date = df['date'][df[df.columns[-1]].last_valid_index()]

    # plotly Figure object
    fig = figure(df, config['hemi'],
                 date=plot_date,
                 plot_mean=config['plot_mean'],
                 plot_stdev=config['plot_stdev'],
                 styles=config['styles'],
                 nstdevs=config['nstdevs'],
                 plot_median=config['plot_median'],
                 plot_iqr=config['plot_iqr'],
                 plot_idr=config['plot_idr'],
                 divisor=config['divisor'],
                 legend_side=config['legend_side'])

    # save the figure to a file
    save_plot('daily_extent', fig, config['output_file'])

    # use imagemagick to create the thumbnail
    name, ext = os.path.splitext(config['output_file'])
    thumbnail_name = '{name}_thumb{ext}'.format(name=name, ext=ext)
    cmd = 'convert -resize 350x280 {file_in} {file_out}'.format(file_in=config['output_file'],
                                                                file_out=thumbnail_name)
    subprocess.run(cmd, shell=True)
    log.info('daily_extent created: %s', thumbnail_name)


if __name__ == '__main__':
    daily_extent()
