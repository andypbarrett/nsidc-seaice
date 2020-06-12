# Upgrading from old packages to the new `seaice`

Initially, the Sea Ice Index software was split across many Python packages. If
your project imported the old packages, you will need to update your
code/configuration to import/install the new package.

## Installation from `environment.yml`

You can either uninstall the old packages from your environment, install
`seaice`, and regenerate `environment.yml`, or just replace the appropriate
lines. For example:

Example:

```
# old
dependencies:
- nasateam=2.5.0=py35_0
- seaicedata=3.6.0=py35_0
- seaicedatastore=1.0.3=py35_0
- seaiceimages=2.5.0=py35_0
- seaicelogging=1.1.1=py35_0
- seaicetimeseries=1.0.7=py35_0


# new
dependencies:
- seaice=1.0.0=py35_0
```

## Installation from `recipe/meta.yaml`

The way to modify your `recipe/meta.yaml` is virtually identical to the
`environment.yml` modification, but `recipe/meta.yaml` is more likely to have
version constraints rather than a pin to a particular version.

Example:

```
# old
requirements:
  build:
    - nasateam >=2.0.0,<3.0.0
    - seaicedatastore >=1.0.0,<2.0.0
  run:
    - nasateam >=2.0.0,<3.0.0
    - seaicedatastore >=1.0.0,<2.0.0


# new
requirements:
  build:
    - seaice >=1.0.0,<2.0.0
  run:
    - seaice >=1.0.0,<2.0.0
```

## Importing new subpackages in Python code

All of the the old packages are now subpackages of `seaice`. For most of them,
this means you simply need to add a `.`:

```
# old
import seaicedata as sid

# new
import seaice.data as sid
```

If you imported without an alias, you can simply add an alias matching the old
package name to avoid making other code changes in your module:

```
# old
import seaicedata

# new
import seaice.data as seaicedata
```

Three of the old packages didn't follow the naming convention, so the new
`import` line is not just adding a `.`, but is still pretty simple:

```
# old
import nasateam as nt
import sea_ice_tools
import sedna

# new
import seaice.nasateam as nt
import seaice.tools as sea_ice_tools
import seaice.sedna as sedna
```
