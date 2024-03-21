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

- A time-varying FMU model input can also be defined
  as a time function of type `Callable[[TimeDurationType], float]`,
  and not only a constant value or a
  [TimeSeries][gemseo_fmu.disciplines.time_series.TimeSeries];
  the documentation provides an example of this functionality.
- The method
  [FMUDiscipline.plot][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.plot]
  draws the temporal evolution of output variables with lines.
- The components of
  [TimeSeries.time][gemseo_fmu.disciplines.time_series.TimeSeries.time]
  can be either strings of characters such as `"2h 34m 5s"`,
  or numbers expressed in seconds
- The arguments `initial_time`, `final_time` and `time_step` of
  [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  can be strings of characters such as `"2h 34m 5s"`,
  in addition to numbers expressed in seconds.
- [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]
  allows to define a time duration
  based on a number expressed in seconds
  or a string of characters such as `"2h 34m 5s"`.

## Changed

- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  stores the time evolution of its time-varying inputs
  in its [local_data][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.local_data]
  when `do_step` is `False`
  and their values at current time otherwise.
- The installation page of the documentation no longer mentions the possibility
  of installing via conda-forge.
- The installation page of the documentation no longer mentions the possibility
  of using gemseo-fmu with Python 3.8.
- The readme file of the project now includes links to the documentation.

## Fixed

- `BaseFMUDiscipline._pre_instantiate` can now redefine time properties
  relative to initial and final times, e.g. simulation time and current value.
- The points of a
  [TimeSeries][gemseo_fmu.disciplines.time_series.TimeSeries]
  are interpreted as the starting points of the intervals of a stairs function
  for FMU model inputs of causality `input`,
  which is consistent with the FMU model input of causality `parameter`.

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