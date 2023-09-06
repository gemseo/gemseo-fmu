<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

GEMSEO-FMU is a [GEMSEO](https://gemseo.readthedocs.io) plugin for
loading, interacting, and simulating Functional Mockup Unit models
(FMUs). FMUs are widely used by the simulation community and can be
generated by over 170 tools such as Dymola, OpenModelica, CATIA, ANSYS,
LS-DYNA, or MATLAB (see the full list here
<https://www.fmi-standard.org/tools>).

GEMSEO-FMU enables the integration and exploitation of FMUs in a
Multidisciplinary Design Optimization (MDO) context, via GEMSEO. For
that, it wraps the FMU model into a GEMSEO discipline named
FMUDiscipline.

GEMSEO-FMU relies on the [FMPy](https://github.com/CATIA-Systems/FMPy)
library for loading the FMU models, setting the model parameters and
evaluating model equations. Model Exchange and Co-Simulation types as
well as versions 1.0, 2.0 and 3.0 of the FMI standard are supported by
FMPy, and so by GEMSEO-FMU.

# Generic examples

Many examples are available to illustrate the main features of
GEMSEO-FMU. See in the examples directory.

# Documentation

The documentation is not yet available.

# Bugs/Questions

Please use the gitlab issue tracker at
<https://gitlab.com/gemseo/dev/gemseo-fmu/-/issues>
to submit bugs or questions.

# License

The **gemseo-fmu** source code is distributed under the GNU LGPL v3.0 license.
A copy of it can be found in the LICENSE.txt file.
The GNU LGPL v3.0 license is an exception to the GNU GPL v3.0 license.
A copy of the GNU GPL v3.0 license can be found in the LICENSES folder.

The **gemseo-fmu** examples are distributed under the BSD 0-Clause, a permissive
license that allows to copy paste the code of examples without preserving the
copyright mentions.

The **gemseo-fmu** documentation is distributed under the CC BY-SA 4.0 license.

The **gemseo-fmu** product depends on other software which have various licenses.
The list of dependencies with their licenses is given in the CREDITS.md file.

# Contributors

- Jorge Camacho Casero
- François Gallard
- Antoine Dechaume
- Matthias De Lozzo
