import os
from distutils.util import strtobool

from invoke import run, task


def this_dir():
    return os.path.dirname(os.path.abspath(__file__))


def parent_dir():
    return os.path.dirname(this_dir())


def output_dir():
    return os.path.join(parent_dir(), 'inv_output')


def shapefile_cmd(mode):
    if mode == 'development':
        cmd = 'python -m seaice.shapefiles.cli.sii_shp'
    else:
        cmd = 'sii_shp'

    return cmd


def print_and_run(cmd):
    cmd_str = ' '.join(cmd.split())
    print(cmd_str)
    return run(cmd_str)


@task
def last_month_polygon(ctx, mode='development', outdir=None):
    """Generate polygon Shapefiles for last month's sea ice extent in both
    hemispheres.

    outdir: directory in which to save the Shapefiles

    """
    if outdir is None:
        outdir = output_dir()
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    print_and_run('{cmd} --monthly --polygon --latest 1 -o {outdir}'.format(cmd=shapefile_cmd(mode),
                                                                            outdir=outdir))


@task
def monthly_polygon(ctx, hemi=None, year=None, month=None, outdir=None, mode='development',
                    all='False'):
    """Generate polygon Shapefiles for monthly sea ice extent.

    hemi: specify N or S to run for just one hemisphere; don't specify to run
        for all hemispheres

    year: specify YYYY to run for just one year; don't specify to run for all
        years

    month: specify MM to run for just one month; don't specify to run for all
        months

    outdir: directory in which to save the Shapefiles

    """
    if outdir is None:
        outdir = output_dir()
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if hemi is None:
        hemis = ['N', 'S']
    else:
        hemis = [hemi]

    if year is None:
        y = ''
    else:
        y = '-y {year}'.format(year=year)

    if month is None:
        m = ''
    else:
        m = '-m {month}'.format(month=month)

    if strtobool(all):
        all = '--all'
    else:
        all = ''

    print_and_run('{cmd} --monthly --polygon -h {hemi} {y} {m} -o {outdir} {all}'.format(
        cmd=shapefile_cmd(mode),
        hemi=','.join(hemis),
        y=y,
        m=m,
        outdir=outdir,
        all=all
    ))


@task
def last_month_polyline(ctx, mode='development', outdir=None):
    """Generate polyline Shapefiles for last month's sea ice extent in both
    hemispheres.

    outdir: directory in which to save the Shapefiles

    """
    if outdir is None:
        outdir = output_dir()
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    print_and_run('{cmd} --monthly --polyline --latest 1 -o {outdir}'.format(
        cmd=shapefile_cmd(mode),
        outdir=outdir)
    )


@task
def monthly_polyline(ctx, hemi=None, year=None, month=None, outdir=None, mode='development',
                     all='False'):
    """Generate polyline Shapefiles for monthly sea ice extent.

    hemi: specify N or S to run for just one hemisphere; don't specify to run
        for all hemispheres

    year: specify YYYY to run for just one year; don't specify to run for all
        years

    month: specify MM to run for just one month; don't specify to run for all
        months

    outdir: directory in which to save the Shapefiles

    """
    if outdir is None:
        outdir = output_dir()
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if hemi is None:
        hemis = ['N', 'S']
    else:
        hemis = [hemi]

    if year is None:
        y = ''
    else:
        y = '-y {year}'.format(year=year)

    if month is None:
        m = ''
    else:
        m = '-m {month}'.format(month=month)

    if strtobool(all):
        all = '--all'
    else:
        all = ''

    print_and_run('{cmd} --monthly --polyline -h {hemi} {y} {m} -o {outdir} {all}'.format(
        cmd=shapefile_cmd(mode),
        hemi=','.join(hemis),
        y=y,
        m=m,
        outdir=outdir,
        all=all
    ))


@task
def daily_median(ctx, hemi=None, dayofyear=None, outdir=None, mode='development', all='False'):
    """Generate climatology polyline Shapefiles for daily sea ice extent.

    hemi: specify N or S to run for just one hemisphere; don't specify to run
        for all hemispheres

    outdir: directory in which to save the Shapefiles

    dayofyear: Specify the day of year to generate climatology for

    """
    median(period='daily', hemi=hemi, dayofyear=dayofyear, outdir=outdir, mode=mode, all=all)


@task
def monthly_median(ctx, hemi=None, month=None, outdir=None,
                   mode='development', all='False'):
    """Generate climatology polyline Shapefiles for monthly sea ice extent.

    hemi: specify N or S to run for just one hemisphere; don't specify to run
        for all hemispheres

    outdir: directory in which to save the Shapefiles

    month: Specify the month to generate climatology for

    """
    median(period='monthly', hemi=hemi, outdir=outdir, mode=mode, all=all, month=month)


def median(period='monthly', hemi=None, dayofyear=None, outdir=None, mode='development',
           all='False', month=None):

    """Generate climatology polyline Shapefiles for monthly/daily sea ice extent.

    hemi: specify N or S to run for just one hemisphere; don't specify to run
        for all hemispheres

    outdir: directory in which to save the Shapefiles

    month: Specify the month to generate climatology for

    dayofyear: Specify the day of year to generate climatology for

    period: Periodicity (monthly, daily) used to generate climatologies

    mode: Specify the mode to pass to shapefile_cmd (e.g. development)

    all: Boolean flag to enable/disable --all flag used in the generation command
    """

    if outdir is None:
        outdir = output_dir()
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if hemi is None:
        hemis = ['N', 'S']
    else:
        hemis = [hemi]

    doy = ''
    if dayofyear is not None:
        doy = '-doy {dayofyear}'.format(dayofyear=dayofyear)

    m = ''
    if month is not None:
        m = '-m {month}'.format(month=month)

    if strtobool(all):
        all = '--all'
    else:
        all = ''

    print_and_run(
        '{cmd} --{period} --median --polyline -h {hemi} {doy} {m} -o {outdir} {all}'.format(
            cmd=shapefile_cmd(mode),
            hemi=','.join(hemis),
            doy=doy,
            outdir=outdir,
            all=all,
            m=m,
            period=period
        )
    )
