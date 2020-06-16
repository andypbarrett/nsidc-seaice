This is a modified version of the NSIDC sea ice CLI and tools.  It has been modified to work on a local directory structure. Routines to read binary sea ice concentration grids into xarray.DataArray and xarray.Dataset objects have been added.  This will make the sea ice data more "Analysis Ready".

TODO
---
Modify setup to set directory path at setup  
Add CLI to package binary grids into netCDF  
Update README with install info for this version.

SeaIce
---

A conda package containing CLIs and subpackages to collect statistics and
perform analysis on sea ice data for the Sea Ice Index, ASINA, and more.

The subpackages used to be independent packages; their old READMEs are available
in `README/`.

If you have a project which uses the old packages and you want to upgrade to
using the new singular package, see [`UPGRADING.md`](UPGRADING.md).

[![CircleCI](https://circleci.com/bb/nsidc/seaice.svg?style=svg)](https://circleci.com/bb/nsidc/seaice)

[![Anaconda-Server Badge](https://anaconda.org/nsidc/seaice/badges/version.svg)](https://anaconda.org/nsidc/seaice)
[![Anaconda-Server Badge](https://anaconda.org/nsidc/seaice/badges/license.svg)](https://anaconda.org/nsidc/seaice)
[![Anaconda-Server Badge](https://anaconda.org/nsidc/seaice/badges/downloads.svg)](https://anaconda.org/nsidc/seaice)
[![Anaconda-Server Badge](https://anaconda.org/nsidc/seaice/badges/installer/conda.svg)](https://conda.anaconda.org/nsidc)

Prerequisites
---

* [Miniconda3](https://conda.io/miniconda.html)

Development
---

Install dependencies:

    $ conda env create -f environment.yml
    $ source activate seaice

Run unit tests:

    $ inv test.unit

Run integration tests -- requires access to the DATASETS share:

    $ inv test.regression

### Updating `environment.yml`

If changes to dependency versions must be made, `environment.yml` should also be
updated. You can start from an environment created from the file and then
install the new packages, and then run update the environment file:

    $ conda install ...  # whatever new versions of packages you want
    $ conda env export > environment.yml

If updating some dependencies and you want to start from scratch to ensure any
unnecessary packages are not included in the environment, create a new
environment, install all of the packages from both the `build` and `run`
sections of `recipe/meta.yaml`, as well as the packages `bumpversion` and
`conda-build`, and run the export command again:

    $ conda create --name seaice
    $ conda install bumpversion conda-build ...  # list all packages from recipe/meta.yaml here
    $ conda env export > environment.yml

Workflow
---

TL;DR:  Use
[GitHub Flow](https://guides.github.com/introduction/flow/index.html).

In more detail:

1. Create a feature branch.
2. Create and push commits on that branch.
3. The feature branch will get built on CircleCI with each push.
4. Update the CHANGELOG with description of changes.
5. Create a Pull Request on BitBucket.
6. When the feature PR is merged, master will get built on CircleCI.

Releasing
---

1. Update the CHANGELOG to list the new version.
2. Add files and commit

        $ git add CHANGELOG.md ...
        $ git commit -m "Release v.X.Y.Z"

3. Bump the version to the desired level:

        $ bumpversion (major|minor|patch)

4. Push

        $ git push origin master --tags

CircleCI will build the conda package and publish it to anaconda.org.

Installing
---
To install and use it in another project:

    $ conda install seaice

Overriding configuration
---

In order to override constants, populate the `OVERRIDE_NASATEAM_CONSTANTS`
environment variable with the path to a YAML file. In a typical NSIDC
deployment, this `overrides.yaml` file exists on the app network share.

Docker
---

This project has had a history of issues with dependencies breaking over time
with no changes to dependency configuration files (`environment.yaml`,
`meta.yaml`). For this reason, we manually push images to
[DockerHub][dockerhub] as a record of working dependencies and as a potential
fallback in case a quick fix is needed.

TODO: Build continuous deployment to DockerHub in addition to Anaconda.org
TODO: Start deploying seaice CLI to production as a Docker image

License
---
See LICENSE file for details.

Important Links
---

* [Bitbucket repo for this package][this-repo]

* [This package on Anaconda][this-anaconda]

* [seaice-vm][seaice-vm] - this repo contains the setup to create and deploy VMs
  for all environments for the Sea Ice Index project

* [Bitbucket project page][bitbucket-all] - see all repos related to the Sea Ice
  Index project

* [Centralized Jenkins CI for whole project][seaice-ci]

* [Dependency Graph view of the whole project CI pipeline][dep-graph]

* [Pivotal][pivotal] - epics and stories for the Sea Ice Index project

* [Trello][trello] - stories tasked out and matched with a cat picture

* [DockerHub][dockerhub] - docker image with seaice and dependencies baked in


[this-repo]: https://bitbucket.org/nsidc/seaice
[this-anaconda]: https://anaconda.org/NSIDC/seaice/files
[seaice-vm]: https://bitbucket.org/nsidc/seaice-vm
[bitbucket-all]: https://bitbucket.org/account/user/nsidc/projects/SI
[seaice-ci]: http://ci.seaice.apps.int.nsidc.org:8080/
[dep-graph]: http://ci.seaice.apps.int.nsidc.org:8080/depgraph-view/
[pivotal]: https://www.pivotaltracker.com/n/projects/1450178
[trello]: https://trello.com/b/ZvYmMHwP/sea-ice-index-services
[dockerhub]: https://hub.docker.com/repository/docker/nsidc/seaice
