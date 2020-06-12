seaiceshapefiles
----------------

**seaiceshapefiles** provides CLI tools to create sea ice extent
[shapefiles][wiki-shapefile](https://en.wikipedia.org/wiki/Shapefile), and
limited API functions for programmatically accessing certain geometry objects
used to create those shapefiles.

![shapefiles](doc/seaiceshapefiles.png)

# Usage

## In other Python modules

These functions are available when this package is imported, e.g.:

```
#!python
import seaice.shapefiles as shp

daily_geom = shp.multipolygon_daily('N', dt.date(2012, 9, 12))
monthly_geom = shp.multipolygon_monthly('N', 2012, 9)
```

For more info, see the API functions docstrings (in the source or with
`help(shp)`).


## CLI Commands

* `sii_shp` - create one or more Shapefiles (.zip with a .shp and other
  files). Use `--help` for full descriptions of the available options.  All
  shapefiles are created from this command.

  - Monthly extent polygon and polylines.

    	sii_shp --monthly --polyline --all
    	sii_shp --monthly --polygon --all

    + default output location:
		* `/share/apps/seaice/shapefiles/{month}/monthly/shapefiles/shp_extent/{MM}_{Mon}/extent_{H}_{YYYY}{MM}_polyline_{ver}.zip`
	    * `/share/apps/seaice/shapefiles/{month}/monthly/shapefiles/shp_extent/{MM}_{Mon}/extent_{H}_{YYYY}{MM}_polygon_{ver}.zip`

  - Climatology day of year extent polylines.

	     sii_shp --daily --median --polyline --all

    + default output location:

		* `/share/apps/seaice/shapefiles/{month}/daily/shapefiles/dayofyear_median/median_extent_{H}_{DOY}_1981-2010_polyline_{ver}.zip`


  - Climatology monthly median extent polylines.

         sii_shp --monthly --median --polyline --all

    + default output location:

      `/share/apps/seaice/shapefiles/{month}/monthly/shapefiles/shp_median/median_extent_{H}_{MM}_1981-2010_polyline_{ver}.zip`
