<!--
 Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

 This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
 International License. To view a copy of this license, visit
 http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
 Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Getting started

GEMSEO-FMU is an extension of the open-source library [GEMSEO](https://www.gemseo.org)
for loading, interacting, and simulating Functional Mockup Unit models (FMUs).
This extension is also open-source,
under the [LGPL v3 license](https://www.gnu.org/licenses/lgpl-3.0.en.html).

[Installation](user_guide/installation.md){ .md-button }

## FMU discipline

The [functional mock-up interface (FMI)](https://fmi-standard.org/)
is a popular free standard to exchange dynamic simulation models.
This standard defines the notion of functional mock-up unit (FMU)
through a ZIP file containg a mix of XML files, binaries and C code.
GEMSEO-FMU proposes
the [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
as a particular [MDODiscipline][gemseo.core.discipline.MDODiscipline]
to simulate an FMU model.

[Read more](user_guide/fmu_discipline.md){ .md-button }
[Examples](generated/examples/fmu_discipline/index.md){ .md-button }
