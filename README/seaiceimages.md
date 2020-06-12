seaiceimages
------------

**seaiceimages** is used to generate images of sea ice from data files in
[NSIDC-0051][0051](https://nsidc.org/data/nsidc-0051) and
[NSIDC-0081][0081](https://nsidc.org/data/nsidc-0081) for use in the [Sea Ice
Index][sii](http://nsidc.org/data/seaice_index/).

![seaiceimages](doc/seaiceimages.png)

# Usage

## CLI

This table details all of the CLI commands included in this package, as well as
a brief description of what they do.  Use the `--help` flag for full descriptions
of all available options.   For output examples, see the graphic in the [Dependencies](# Dependencies) section

| CLI                           | Description
|-------------------------------|------------
|`sii_image`                    | Generates standard extent/concentration and trend/anomaly images for a variety of ranges/dates
|`sii_image_sos`                | Generates 'science on a spehere' images
|`sii_image_google_earth`       | Generates 'google earth' images
|`sii_image_latest`             | Helper command to generate 'latest' images for all types.  This command wraps the other commands
|`sii_image_geotiff`            | Generates extent, concentration and anomaly GeoTiff images.
| `sii_image_seasonal`          | Use with `--trend` to generate seasonal concentration trend images. See [Trello](https://trello.com/c/O2YSjV9L) for more details.

# Development

Updates that fundamentally change the image being generated should include an
update to the smoke test reference images
(source/seaiceimages/test/test_smoke/reference_images)
