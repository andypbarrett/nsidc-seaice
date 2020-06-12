import seaice.nasateam as nt
from . import geom
from . import grids


def _get_grid(config, contour_value):
    """Returns a binary grid of 1/0's to create polygons of."""
    if contour_value is None:
        keep_flags = False
    else:
        keep_flags = True

    grid = grids.grid(config, keep_flag_values=keep_flags)

    if keep_flags:
        grid = (grid == contour_value).astype('uint8')

    return grid


def multipolygon_daily(hemi, date, contour_value=None):
    """Return a shapely MultiPolygon object for sea ice extent for the given
    date.

    hemi: 'N' or 'S'

    date: datetime.date

    contour_value: Optional pixel value to create contours for.
        e.g., contour_value=255 returns contours of missing data.

    """
    config = {
        'daily': True,
        'hemi': nt.by_name(hemi),
        'search_paths': nt.DEFAULT_SEA_ICE_PATHS,
        'extent_threshold': nt.EXTENT_THRESHOLD,
        'year': date.year,
        'month': date.month,
        'day': date.day
    }

    grid = _get_grid(config, contour_value)

    return geom.multipolygon_from_grid(grid, config)


def multipolygon_monthly(hemi, year, month, contour_value=None):
    """Return a shapely MultiPolygon object for sea ice extent for the given
    month.

    hemi: 'N' or 'S'

    year: int

    month: int

    contour_value: Optional pixel value to create contours for.
        e.g., contour_value=255 returns contours of missing data.

    """
    config = {
        'monthly': True,
        'hemi': nt.by_name(hemi),
        'search_paths': nt.DEFAULT_SEA_ICE_PATHS,
        'extent_threshold': nt.EXTENT_THRESHOLD,
        'year': year,
        'month': month
    }

    grid = _get_grid(config, contour_value)

    return geom.multipolygon_from_grid(grid, config)
