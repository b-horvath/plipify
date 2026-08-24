#!/usr/bin/env bash

# $CI_OS is $matrix.os, as exported in GHA *.yaml
# $CONDA (miniconda installation path) is always defined in the GHA virtual environments

# Ensure that YAML parser is present before we run python scripts
python -m pip install --quiet pyyaml

case ${CI_OS} in
    windows*)
        eval "$(${CONDA}/condabin/conda.bat shell.bash hook)";;
    *)
        eval "$(${CONDA}/condabin/conda shell.bash hook)";;
esac