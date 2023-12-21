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

# Version 2.0.0 (December 2023)

## Added

- Support for Python 3.11.
- The default behavior of
  [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  is either simulating until the final time or during a time step;
  it can also restart from initial time after each execution.
- [FMUDiscipline.execute][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute]
  can change the behavior of the
  [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  temporarily, to simulate during a given simulation time, with a
  different time step or from initial time.
- [TimeSeries][gemseo_fmu.disciplines.time_series.TimeSeries]
  allows to specify inputs as time series.
- [gemseo-fmu.problems][gemseo_fmu.problems] contains use cases,
  either defined as [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  or simply as FMU files;
  use [get_fmu_file_path][gemseo_fmu.problems.fmu_files.get_fmu_file_path]
  to get a FMU file path easily.
- [DoStepFMUDiscipline][gemseo_fmu.disciplines.do_step_fmu_discipline.DoStepFMUDiscipline]
  is an [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  whose execution is only one time step ahead.
- [DoStepFMUDiscipline][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  is a system of static and time-stepping disciplines
  which executes them sequentially at each time step.

## Changed

- The [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  relies on the library [FMPy](https://github.com/CATIA-Systems/FMPy).
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  is in [gemseo-fmu.disciplines][gemseo_fmu.disciplines].

## Removed

- Support for Python 3.8.

# Version 1.0.1 (June 2023)

Update to GEMSEO 5.

# Version 1.0.0 (January 2023)

First release.
