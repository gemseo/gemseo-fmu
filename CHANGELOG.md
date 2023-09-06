<!--
Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

<!--
Changelog titles are:
- Added: for new features.
- Changed: for changes in existing functionality.
- Deprecated: for soon-to-be removed features.
- Removed: for now removed features.
- Fixed: for any bug fixes.
- Security: in case of vulnerabilities.
-->

# Changelog

All notable changes of this project will be documented here.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0)
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Develop

## Added

- The default behavior of `.FMUDiscipline`{.interpreted-text
    role="class"} is either simulating until the final time or during a
    time step; it can also restart from initial time after each
    execution.
- `.FMUDiscipline.execute`{.interpreted-text role="class"} can change
    the behavior of the `.FMUDiscipline`{.interpreted-text role="class"}
    temporarily, to simulate during a given simulation time, with a
    different time step or from initial time.
- `.TimeSeries`{.interpreted-text role="class"} allows to specify
    inputs as time series.
- `gemseo-fmu.use_cases`{.interpreted-text role="meth"} contains use
    cases, either defined as `.FMUDiscipline`{.interpreted-text
    role="class"} or simply as FMU files; use
    `get_fmu_file_path`{.interpreted-text role="func"} to get a FMU file
    path easily.

## Changed

- The `.FMUDiscipline`{.interpreted-text role="class"} relies on the
    library [FMPy](https://github.com/CATIA-Systems/FMPy).
- `.FMUDiscipline`{.interpreted-text role="class"} is in
    `gemseo-fmu.disciplines`{.interpreted-text role="mod"}.

# Version 1.0.1 (June 2023)

Update to GEMSEO 5.

# Version 1.0.0 (January 2023)

First release.
