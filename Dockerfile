FROM continuumio/miniconda:4.6.14

RUN conda create -n seaice seaice=2.3.0 \
    -c nsidc -c conda-forge -c defaults

ENTRYPOINT ["conda", "run", "-n", "seaice"]
