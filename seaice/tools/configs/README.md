# YAML configuration for `plot_daily_ice_extent`

Most of the CLI options can be defined here in a fairly straightforward way. The
options to watch out for are `legend`, `years` and:

* `month_bounds`: on the CLI, "-3,1"; in the YAML, use a proper array, e.g.,
  `[-3, 1]`. Same goes for `percentiles`.
* `plot_mean`: on the CLI, `--plot_mean` or `--no-plot_mean`; in the YAML, just
  set `plot_mean` to `true` or `false`. Same goes for all of the other "to plot
  or not to plot" flags.

## legend

There is a flag to set the legend to the right or left side regardless of data
on the graph, e.g., `--legend_side=left`. This can be customized by month in the
yaml:

```
legend:
  10:
    legend_side: 'left'
```

This would guarantee that for graphs where the "focus date" is October, the
legend will be placed on the left side; otherwise, it will be placed on a side
that should keep it from overlapping with data.

## years

On the CLI, years are simply listed, `--years=2014,record_low_year,current`.

In the YAML, styling for a year line goes along with the list:

```
years:
  record_low_year:
    color: rgb(3, 88, 38)
    dash: dot
  2014:
    color: rgb(255, 0, 0)
```

This ensures that the record low year will be drawn with a dashed dark green
line, and 2014 will be plotted with a bright red line. The style values that are
set for each year (here `color` and `dash`) are directly passed to the Plotly
line settings. Other settings are `smoothing`, `width`, and `shape`. The full
descriptions of these values is available in
[Plotly's documentation](https://plot.ly/python/reference/#scatter-line).

To include a year with no special styling:

```
years:
  2013: {}
```

All years listed in the YAML file will be included in the plot, as if they were
given as the list with the `--years` CLI argument. If `--years` is explicitly
given on the CLI, then the list of years in the yaml config will be ignored, but
the styling will still be used.

For example, with this yaml config:

```
years:
  record_low_year:
    color: rgb(3, 88, 38)
    dash: dot
  2014:
    color: rgb(255, 0, 0)
```

Running `plot_daily_ice_extent --years=record_low_year,2013` will result in a
plot with the record low year represented with a dark green dashed line, and
2013 will be styled according to Plotly defaults.
