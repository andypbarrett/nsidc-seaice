import numpy as np

import seaice.nasateam as nt


class ConcentrationCube(object):
    """Wrapper around a numpy data cube, where each layer in the cube is a
    concentration grid at a different time.

    Instance Variables:
    -------------------

    cube: numpy 3D-array to treat as a cube of stacked grids.  The dimensions
        are rows, columns, number_grids. Values within the valid_data_range
        represent ice cover. Values outside of the range are special flag
        values.

    data_cube: numpy masked array; the same as cube, but values outside of the
        valid_data_range are not considered valid ice, and are masked.

    missing_value: Placeholder value meaning no valid observation occurred
        and is ignored where possible.

    invalid_data_mask: Boolean numpy 2D-array grid whose shape matches a
        cube-layer that describes locations that are excluded from area, extent
        and missing calculations. True values represent gridcells that are
        considered invalid.  For example, invalid ice masks used in sea ice
        processing. (https://nsidc.org/data/nsidc-0622)

    grid_areas: numpy 2D-array whose shape matches a ConcentrationCube layer and
        whose values are the grid cell areas.  For example if you are working
        with Nasateam data the northern hemisphere areas would come from
        'psn25area_v3.dat' in units of square kilometers.
        (https://nsidc.org/data/polar_stereo/tools_geo_pixel.html)

    extent_threshold: Minimum value in the data grid that to be included in
        extent and area calculations. Many people think of this as the "cutoff
        value". For example, sea ice concentrations under 15% are not counted in
        area and extent; in that case, extent_threshold would be set to 15.

    flags: Dict describing special placeholder values. Key/value pairs are
        name/data value. A 'pole' key must be included; see pole_hole_value.

    pole_hole_value: Placeholder value in input data that should be counted
        as part of the extent even if masked, but not as part of the area.

    valid_data_range: Tuple containing the lower and upper bounds of valid data
        values. Values outside of this range are treated as flag values, even if
        they are not described by the flags property.

    mean_data_grid: numpy 2D-array where each gridcell has the mean value of the
        gridcells throughout each layer of the cube. Flag and missing values are
        ignored in this calculation. Calculated on initialization for efficient
        reuse.

    missing_binary_grid: numpy 2D-array of 1's and 0's; 1 indicates the gridcell
        has missing values throughout the cube. Calculated on initialization for
        efficient reuse.

    missing_grid: numpy 2D-array where the values represent the amount of area
        each gridcell contributes toward the total missing; 0 if data is not
        missing, or the area of the gridcell. Calculated on initialization for
        efficient reuse.

    area_grid: numpy 2D-array where the values represent the amount of area each
        gridcell contributes toward the total area; 0 if the concentration is
        too low or the value is missing or invalid, or the area of the gridcell
        multiplied by the percentage of the concentration in that
        gridcell.. Calculated on initialization for efficient reuse.

    extent_grid: numpy 2D-array where the values represent the amount of area
        each gridcell contributes toward the total extent; 0 if the
        concentration is too low or the value is missing or invalid, or the area
        of the gridcell. Calculated on initialization for efficient reuse.

    Public Methods:
    ---------------
    area         -- total area covered by the concentration
    extent       -- total area of grid cells where concentration is at least the
                    threshold
    grid_shape   -- tuple representing the shape of one layer in the cube
    missing      -- total area of grid cells where concentration is missing

    """

    def __init__(self, data, missing_value=nt.FLAGS['missing'], invalid_data_mask=None,
                 grid_areas=None, extent_threshold=0.0, valid_data_range=(0, 100),
                 flags=nt.FLAGS):
        """Initialize a ConcentrationCube instance from a numpy nd-array.

        Positional Arguments:
        ---------------------
        data -- a numpy nd-array to treat as a cube. It should have either 2 or
                3 dimensions. If it is just a 2D grid, it is dstacked and stored
                as a cube with height of 1. Values should be between 0 and 100,
                representing fractional ice cover as percent coverage.

        Keyword Arguments:
        ------------------
        - Properties set by keyword argument.  See Class documentation.
           -- missing_value. Defaults to numpy.nan
           -- invalid_data_mask. Defaults to all False.
           -- grid_areas. Defaults to all 1.
           -- extent_threshold. Defaults to 0.
           -- flags. Must include a 'pole' key/value pair. Defaults to nt.FLAGS.
           -- valid_data_range. Defaults to (0., 100.).

        """
        self.cube = np.ma.dstack([data]) if data.ndim == 2 else data
        self.missing_value = missing_value
        self.extent_threshold = extent_threshold
        self.invalid_data_mask = self._invalid_data_mask(invalid_data_mask)
        self.grid_areas = self._grid_areas(grid_areas)
        self.pole_hole_value = flags['pole']
        self.valid_data_range = valid_data_range

        self.data_cube = np.ma.masked_outside(self.cube, *self.valid_data_range)

        self.mean_data_grid = np.ma.mean(self.data_cube, axis=2)

        self.missing_binary_grid = self._missing_binary_grid()

        self.missing_grid = self._missing_grid()
        self.area_grid = self._area_grid()
        self.extent_grid = self._extent_grid()

    def area(self, regional_mask=None):
        """Returns the total area of ice, in the units of the reference grid.
        Differs from extent in that for each grid cell, the area of the grid
        cell is multiplied by the fractional area of ice in that cell. In
        other words, if the ice covers 80% of a grid cell, the value
        returned by area is 80% of the area of the grid cell.

        Keyword Arguments:
        ------------------
        regional_mask: numpy 2d mask describing a masked region of interest;
            gridcells in the region are False, gridcells outside of the
            region are True. Defaults to all False, i.e., mask nothing.

        """
        return self._sum(np.ma.masked_array(self.area_grid, regional_mask))

    def extent(self, regional_mask=None):
        """Returns the total extent of ice cover, in the units of the reference grid.

        Keyword Arguments:
        ---------------------
        regional_mask: numpy 2d mask describing a masked region of interest;
            gridcells in the region are False, gridcells outside of the
            region are True. Defaults to all False, i.e., mask nothing.

        """
        return self._sum(np.ma.masked_array(self.extent_grid, regional_mask))

    def grid_shape(self):
        """Returns the shape of one layer in the cube."""
        return self.cube.shape[0:2]

    def missing(self, regional_mask=None):
        """Returns the total area of grid cells whose value is the
        missing_data_value, in the units of the reference grid.

        Keyword Arguments:
        ------------------
        regional_mask: numpy 2d mask describing a masked region of interest;
            gridcells in the region are False, gridcells outside of the
            region are True. Defaults to all False, i.e., mask nothing.

        """
        return self._sum(np.ma.masked_array(self.missing_grid, regional_mask))

    def _area_binary_grid(self):
        """Returns a binary grid with 1 meaning the gridcell should be included in the
        area calculation, and 0 meaning it should not be included.

        """
        return self._extent_binary_grid(include_pole_hole=False)

    def _area_grid(self):
        return self._area_binary_grid() * self.grid_areas * (self.mean_data_grid / 100.0)

    def _extent_binary_grid(self, include_pole_hole=True):
        """Returns a grid of 0's and 1's representing whether the average concentration
        value in the cube is at least self.extent_threshold. Gridcells whose
        values are missing or other flagged values are masked; gridcells whose
        values are valid concentrations, but below the extent threshold, are
        unmasked and have a value of 0.

        Positional Arguments:
        ---------------------
        include_pole_hole: whether pole hole grid cells in the returned
          extent grid should have a value of 1

        """
        total_extent_grid = self.mean_data_grid >= self.extent_threshold

        if include_pole_hole:
            # True in the pole hole, False everywhere else
            pole_hole_bool_grid = np.ma.all(self.cube.data == self.pole_hole_value, axis=2)

            # add pole hole to total_extent_grid.data; total_extent_grid.mask is unaffected
            total_extent_grid = np.logical_or(total_extent_grid, pole_hole_bool_grid)

            # update the mask now; unmask the pole hole
            try:
                total_extent_grid.mask[pole_hole_bool_grid] = False
            except TypeError:
                pass

        total_extent_grid = np.ma.masked_array(total_extent_grid, mask=self.missing_binary_grid)

        return self._mask_invalid(total_extent_grid).astype(np.int)

    def _extent_grid(self):
        return self._extent_binary_grid(include_pole_hole=True) * self.grid_areas

    def _grid_areas(self, grid_areas):
        """Returns either input grid_areas or a default all 1.0 area grid."""
        if grid_areas is None:
            return np.ones(self.grid_shape())

        if self.grid_shape() != grid_areas.shape:
            raise ValueError('Grid areas shape must match input data grid layer.')

        return grid_areas

    def _invalid_data_mask(self, invalid_data_mask):
        """Returns either input invalid_data_mask or a default all False data mask."""
        if invalid_data_mask is None:
            return np.zeros(self.grid_shape(), dtype=bool)

        if self.grid_shape() != invalid_data_mask.shape:
            raise ValueError('Mask shape must match input data grid layer.')

        return invalid_data_mask

    def _mask_invalid(self, grid):
        """Mask any data in the invalid_data_mask. """
        return np.ma.masked_array(grid, mask=self.invalid_data_mask)

    def _missing_binary_grid(self):
        """ Returns boolean grid that is True when every gridcell's layer value is missing."""
        return self._mask_invalid(np.ma.all(self.cube.data == self.missing_value, axis=2))

    def _missing_grid(self):
        return self.missing_binary_grid.astype(np.int) * self.grid_areas

    def _sum(self, grid):
        total = np.ma.sum(grid)
        if total is np.ma.masked:
            total = np.nan
        return np.float(total)
