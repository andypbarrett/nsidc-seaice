"""Functions for making xarray.Dataset objects of sea ice data
"""
import xarray as xr
import pandas as pd
import numpy as np

from affine import Affine

from .api import concentration_daily
import seaice.nasateam as nt


def affine_transform(hemisphere):
    """Returns affine transformation matrix"""
    return Affine(hemisphere['transformation_constants']['scale_x'],
                  0,
                  hemisphere['transformation_constants']['offset_x'],
                  hemisphere['transformation_constants']['scale_y'],
                  0,
                  hemisphere['transformation_constants']['offset_y']) 


def grid_coordinates(hemisphere):
    """Returns x and y grid coordinates in meters"""
    fwd = affine_transform(hemisphere)
    x = [(fwd * (i+0.5, 0))[0] for i in np.arange(hemisphere['cols'])]
    y = [(fwd * (0, j+0.5))[0] for j in np.arange(hemisphere['rows'])]
    return x, y

    
def concentration_daily_as_xarray(hemisphere, date, search_paths, apply_filter=True, **kwargs):
    """Returns a sea concentration gridset as an xarray.DataArray with time and projected x, y 
       coordinates, and attributes
       """
    x, y = grid_coordinates(hemisphere)
    x_da = xr.DataArray(x, coords={'x': x}, dims=['x'],
                     attrs={'long_name': 'x', 'units': 'm'})
    y_da = xr.DataArray(y, coords={'y': y}, dims=['y'], 
                     attrs={'long_name': 'y', 'units': 'm'})
    
    gridset = concentration_daily(hemisphere, date.year, date.month, date.day,
                                      search_paths, **kwargs) 
    da = xr.DataArray(np.expand_dims(gridset['data'], 0),
                      coords={
                          'time': [gridset['metadata']['period'].to_timestamp()],
                          'x': x_da,
                          'y': y_da},
                      dims=['time', 'y', 'x'],
                      attrs = {'long_name': 'sea ice concentration',
                               'units': '%',
                               'source': 'NSIDC-0051'}) 

    if apply_filter:
        da = da.where(da < 100., np.nan)  # mask missing values, and land,
                                           #coast, pole hole and unused pixel values
    
    return da 


def concentration_daily_for_year_to_dataset(hemisphere, year, search_paths, apply_filter=True):
    """Returns a xarray.Dataset containing a year of sea ice concentrations"""
    # TODO: add lat and lon
    dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='D')
    da = xr.concat([concentration_daily_as_xarray(hemisphere, d,
                                                  search_paths,
                                                  apply_filter=True) for d in dates], 'time')
    return da.to_dataset(name='sic')

