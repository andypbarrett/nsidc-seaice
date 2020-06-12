import os

from invoke import task, run
import yaml

from . import dirs


def plotter_cmd(mode):
    if mode == 'development':
        cmd = 'python ' + os.path.join(dirs.parent_dir(), 'seaice.tools',
                                       'plotter', 'monthly_extent.py')
    else:
        cmd = 'plot_monthly_ice_extent'

    return cmd


def plotter_anomalies_cmd(mode):
    if mode == 'development':
        cmd = 'python ' + os.path.join(dirs.parent_dir(), 'seaice.tools',
                                       'plotter', 'monthly_anomaly.py')
    else:
        cmd = 'plot_monthly_ice_anomaly'

    return cmd


def plotter_daily_extents_cmd(mode):
    if mode == 'development':
        cmd = 'python ' + os.path.join(dirs.parent_dir(), 'seaice.tools',
                                       'plotter', 'daily_extent.py')
    else:
        cmd = 'plot_daily_ice_extent'

    return cmd


@task
def plot_monthly_extents(ctx, mode='development',
                         hemisphere=None,
                         data_store=os.path.join(dirs.datastore_directory(), 'monthly.p'),
                         output_dir=dirs.output_image_dir()):
    """
    Create extent graphs for each month from sedna's monthly output
    """
    os.makedirs(output_dir, exist_ok=True)

    if hemisphere is None:
        hemis = ['N', 'S']
    else:
        hemis = [hemisphere]

    for hemi in hemis:
        for month in range(1, 12 + 1):
            cmd = '{cmd} -h {hemi} -m {month} {data_store} {output_dir}'.format(
                cmd=plotter_cmd(mode),
                hemi=hemi,
                month=month,
                data_store=data_store,
                output_dir=output_dir)
            print(cmd)
            run(cmd)


daily_plot_config_files = [
    'asina_north.yaml',
    'asina_south.yaml',
    'north.yaml',
    'south.yaml',
    'asina_north_iqr.yaml',
    'asina_south_iqr.yaml',
    'north_iqr.yaml',
    'south_iqr.yaml'
]


@task
def plot_daily_extents(ctx, mode='development',
                       data_store=os.path.join(dirs.datastore_directory(), 'daily.p'),
                       output_dir=dirs.output_image_dir()):
    """Create the daily timeseries standard north/south plots, and custom ASINA (standard north
    plus a few years) daily sea ice extent plots.

    """

    run('mkdir -p {0}'.format(output_dir))

    for config_filename in daily_plot_config_files:
        config_file = os.path.join(dirs.default_config_dir(), config_filename)

        cmd = '{cmd} -c {conf} --output_dir={output_dir}'.format(
            cmd=plotter_daily_extents_cmd(mode),
            conf=config_file,
            output_dir=output_dir
        )
        print(cmd)
        run(cmd)


@task
def plot_daily_extents_all_the_months(ctx, mode='development',
                                      data_store=os.path.join(dirs.datastore_directory(),
                                                              'daily.p'),
                                      output_dir=dirs.output_image_dir()):
    """For every month: Create the standard north, standard south, and custom ASINA (standard north
    plus a few years) daily sea ice extent plots.

    """

    run('mkdir -p {0}'.format(output_dir))

    for config_filename in daily_plot_config_files:
        config_file = os.path.join(dirs.default_config_dir(), config_filename)

        with open(config_file, 'r') as fp:
            config_yaml = yaml.load(fp)

        for month in range(1, 12 + 1):
            date = '2015-{mm:02}-01'.format(mm=month)

            filename, extension = os.path.splitext(config_yaml['output_file'])

            output_filename = '{}_{:02}{}'.format(filename, month, extension)
            output_file = os.path.join(output_dir, output_filename)

            cmd = '{cmd} -c {conf} --output_file={output_file} --date={date}'.format(
                cmd=plotter_daily_extents_cmd(mode),
                conf=config_file,
                output_file=output_file,
                date=date)
            print(cmd)
            run(cmd)


@task
def plot_anomalies(ctx, mode='development',
                   hemisphere=None,
                   month=None,
                   hires=False,
                   version=None,
                   data_store=os.path.join(dirs.datastore_directory(), 'monthly.p'),
                   output_dir=dirs.output_image_dir()):
    """
    Create extent anomaly graphs for each month from sedna's monthly output
    """
    os.makedirs(output_dir, exist_ok=True)

    if month is None:
        month = range(1, 12+1)
    else:
        month = month.split(',')

    if hemisphere is None:
        hemis = ['N', 'S']
    else:
        hemis = hemisphere.split(',')

    version_string = ''
    if version is not None:
        version_string = '-v {}'.format(version)

    hires_str = '--hires' if hires else ''

    for hemi in hemis:
        for month_num in month:
            cmd = '{cmd} -h {hemi} -m {month} {version} {hires} {data_store} {output_dir}'.format(
                cmd=plotter_anomalies_cmd(mode),
                hemi=hemi,
                month=month_num,
                version=version_string,
                hires=hires_str,
                data_store=data_store,
                output_dir=output_dir)
            print(cmd)
            run(cmd)


@task(default=True)
def all(ctx, mode='development', output_root_dir=dirs.output_image_dir()):
    """
    Plot daily_extents, monthly_extents, and anomalies.
    """
    plot_monthly_extents(ctx, mode, output_dir=output_root_dir)
    plot_anomalies(ctx, mode, output_dir=output_root_dir)
    plot_daily_extents(ctx, mode, output_dir=output_root_dir)
