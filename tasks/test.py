# import os

from invoke import task
import musher
from musher.test import flake8

# from seaice.nasateam import VERSION_STRING as version
# from seaice.tools.reader import read


@task(flake8)
def build(ctx, logs=False):
    """
    run flake8 and unittests using nose
    """
    unit(ctx, logs=logs)


@task
def unit(ctx, logs=False):
    """
    run unittests using nose
    """
    musher.test.unit(
        ctx,
        logs=logs,
        exclude_dirs=[
            'seaice/data/test/test_regression',
            'seaice/images/test/test_smoke',
            'seaice/shapefiles/test/test_smoke',
            'seaice/sedna/test/test_regression'
        ]
    )


@task
def regression(ctx, logs=False):
    """
    run all regression/smoke tests using nose
    """
    smoke_shp(ctx, logs=logs)
    regression_seaicedata(ctx, logs=logs)
    regression_sedna(ctx, logs=logs)
    smoke_img(ctx, logs=logs)


@task
def regression_sedna(ctx, logs=False):
    """
    run sedna regression tests using nose
    """
    musher.test.unit(ctx, where='seaice/sedna/test/test_regression', logs=logs)


@task
def regression_seaicedata(ctx, logs=False):
    """
    run sedna regression tests using nose
    """
    musher.test.unit(ctx, where='seaice/data/test/test_regression', logs=logs)


@task
def smoke_shp(ctx, logs=False):
    """
    run shapefile smoke tests using nose
    """
    musher.test.unit(ctx, where='seaice/shapefiles/test/test_smoke', logs=logs)


@task
def smoke_img(ctx, logs=False):
    """
    run image smoke tests using nose
    """
    musher.test.unit(ctx, where='seaice/images/test/test_smoke', logs=logs)


@task(flake8, default=True)
def all(ctx, logs=False):
    """
    run all of the tests
    """
    unit(ctx, logs=logs)
    regression(ctx, logs=logs)


# # from seaice.tools
# @task
# def reader(ctx):
#     """
#     Test the reader by simply calling read() with all the files that it should
#     work with; requires first running the tasks `xlsx.all` and `csvs.all`.
#     """

#     files = [
#         'test_output/Sea_Ice_Index_Daily_Extent_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Min_Max_Rankings_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Monthly_Data_by_Year_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Monthly_Data_with_Statistics_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Rates_of_Change_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Regional_Daily_Data_G02135_{}.xlsx'.format(version),
#         'test_output/Sea_Ice_Index_Regional_Monthly_Data_G02135_{}.xlsx'.format(version),

#         'test_output/monthly_csv/south/monthly/data/S_08_extent_{}.csv'.format(version),
#         'test_output/north/daily/data/N_seaice_extent_climatology_1981-2010_{}.csv'.format(version),
#         'test_output/south/daily/data/S_seaice_extent_daily_{}.csv'.format(version)
#     ]

#     for filename in files:
#         print('reading {}...'.format(os.path.basename(filename)))
#         read(filename)
