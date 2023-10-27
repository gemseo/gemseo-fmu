<!--
 Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

 This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
 International License. To view a copy of this license, visit
 http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
 Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Installation

## Basics

### Requirements

To install GEMSEO-FMU,
you should use a Python environment.
You can create environments with
the Python built-in
[venv](https://docs.python.org/3.9/library/venv.html) module
or with [anaconda](https://docs.anaconda.com/anaconda/install).

### Install from Pypi

Install the latest version with

```bash
pip install gemseo-fmu
```

See [pip](https://pip.pypa.io/en/stable/getting-started/) for more information.

### Install from Anaconda

Install the latest version
in an anaconda environment named *gemseo-fmu* for Python 3.9 with

```bash
conda create -c conda-forge -n gemseo-fmu python=3.9 gemseo-fmu
```

You can change the Python version to 3.8 or 3.10.

## Test the installation

### Basic test

To check that the installation is successful,
try to import the module:

```bash
python -c "import gemseo_fmu"
```

If you obtain an error as `ImportError: No module named gemseo-fmu`,
then the installation failed.

### Test with examples

The [gallery of examples](../generated/examples/index.md) contains
many examples to illustrate the main features of GEMSEO-FMU.
For each example,
you can download a Python script or a Jupyter Notebook,
execute it and experiment to test the installation.

## Advanced

### Install the development version

Install the development version with

```bash
pip install gemseo-fmu@git+https://gitlab.com/gemseo/dev/gemseo-fmu.git@develop
```

To develop in GEMSEO-FMU,
see instead the [contributing section of GEMSEO](https://
gemseo.readthedocs.io/en/stable/software/developing.html#dev).

### Test with unit tests

Run the tests with:

```bash
pip install gemseo-fmu[test]

```

Look at the output of the above command
to determine the installed version of GEMSEO-FMU.
Get the tests corresponding to the same version of GEMSEO-FMU from
[gitlab](https://gitlab.com/gemseo/dev/gemseo-fmu>).
Then from the directory of this archive that contains the `tests` directory,
run

```bash
pytest
```

Look at the [contributing section of GEMSEO](https://
gemseo.readthedocs.io/en/stable/software/developing.html#dev)
for more information on testing.
