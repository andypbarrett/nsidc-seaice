#!/bin/bash
set -xe

conda config --add channels conda-forge
conda config --add channels nsidc

conda create -n build
source activate build

conda install -y "conda-build >=2.0.0,<3.0.0a" "anaconda-client=1.6.*" "invoke=0.13.*" "musher=0.6.*"
