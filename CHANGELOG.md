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

## Version 3.1.1 (October 2025)

### Fixed

- [BaseFMUDiscipline][gemseo_fmu.disciplines.base_fmu_discipline.BaseFMUDiscipline] no longer raises an exception when the time variable is defined in `modelVariables` of the _modelDescription.xml_ file.

### Added

- Support for Python 3.13.

### Removed

- Support for Python 3.9.

## Version 3.1.0 (August 2025)

### Added

- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] supports the variable types `Int32`, `Int64`, `Float64`, `Boolean`, `String` and `Enumeration` introduced by FMI3.
- [TimeSeries.compute][gemseo_fmu.utils.time_series.TimeSeries.compute] is a piecewise linear function when its field ``interpolate`` is ``True``.
- [TimeSeries.from_csv][gemseo_fmu.utils.time_series.TimeSeries.from_csv] is used to create a [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries] from a CSV file.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem] has a new option ``mda_max_iter_at_t0`` to perform an MDA at initial time with at most ``mda_max_iter_at_t0`` iterations.
- [FMUDiscipline.set_default_execution][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.set_default_execution] has a new option ``initialize_only`` to simply initialize the FMU model at execution.
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] has a new argument, named ``time_name``, to set the name of the time variable (default: ``"time"``).
- [FMUDiscipline.set_default_execution][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.set_default_execution] has a new argument, named ``use_arrays_only``, to pass only NumPy arrays at execution (default: ``False``).
- The function [plot_time_evolution][gemseo_fmu.utils.plotting.plot_time_evolution] draws the time evolution of a collection of variables.
- The `time_window` argument of the method [FMUDiscipline.plot][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.plot]
  can also be a float number defining the initial time or a tuple of float numbers defining the initial and final times.

### Fixed

- [BaseFMUDiscipline][gemseo_fmu.disciplines.base_fmu_discipline.BaseFMUDiscipline] supports array outputs (FMI3 only).
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] supports FMI3 when ``do_step`` is ``True``
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] supports FMI3 when using the default input data.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem] supports input data passed as numbers.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem] supports Gauss-Seidel as co-simulation algorithm.

### Changed

- The time variable of [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] is no longer namespaced _but_ still prefixed by the discipline name: ``f"{discipline_name}_{time_name}"``.

## Version 3.0.0 (November 2024)

### Added

- Support GEMSEO v6.
- Support for Python 3.12.
- The class [TimeManager][gemseo_fmu.utils.time_manager.TimeManager] can be used to create a time manager
  from an initial time, a final time and a time step;
  the current time can be updated
  with the [update_current_time][gemseo_fmu.utils.time_manager.TimeManager.update_current_time] method
  and reset with the [reset][gemseo_fmu.utils.time_manager.TimeManager.reset] one.
- The method
  [FMUDiscipline.set_default_execution][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.set_default_execution]
  can be used to redefine some default settings, such as `do_step`, `final_time`, `restart` and `time_step`.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  has new arguments `mda_name` and `mda_options` to define the master algorithm,
  e.g. a parallel master algorithm inspired by the Jacobi method when `mda_name="MDAJacobi"` (default)
  and a serial one inspired by the Gauss-Seidel method when `mda_name="MDAGaussSeidel"`.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  has a new argument `apply_time_step_to_disciplines` (default: `True`);
  if `True`,
  the value of its `time_step` argument is passed to the time-stepping disciplines;
  otherwise,
  the time-stepping disciplines use their own time steps.
- Any [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline] can use scalar input variables.
- A time-varying FMU model input can also be defined
  as a time function of type `Callable[[TimeDurationType], float]`,
  and not only a constant value or a
  [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries];
  the documentation provides an example of this functionality.
- The method
  [FMUDiscipline.plot][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.plot]
  draws the temporal evolution of output variables with lines.
- The components of
  [TimeSeries.time][gemseo_fmu.utils.time_series.TimeSeries.time]
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
- The `variable_names` argument of [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  allows the discipline to have input and output names different from the input and output names of the FMU model.

### Changed

- [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries] is now
  in the subpackage [gemseo_fmu.utils.time_series][gemseo_fmu.utils.time_series].
- [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries] supports the `==` and `!=` operators.
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  stores the time evolution of its time-varying inputs
  in its [local_data][gemseo.core.discipline.base_discipline.BaseDiscipline.local_data]
  when `do_step` is `False`
  and their values at current time otherwise.
- The installation page of the documentation no longer mentions the possibility
  of installing via conda-forge.
- The installation page of the documentation no longer mentions the possibility
  of using gemseo-fmu with Python 3.8.
- The readme file of the project now includes links to the documentation.

### Fixed

- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  can use input values of type [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries].
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  can simulate up to the final time by adapting the last time step
  in the case where the difference between the initial and final times is not a multiple of the time step.
- [FMUDiscipline.set_next_execution][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.set_next_execution]
  can be called several times before an execution.
- `BaseFMUDiscipline._pre_instantiate` can now redefine time properties
  relative to initial and final times, e.g. simulation time and current value.
- The points of a
  [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries]
  are interpreted as the starting points of the intervals of a stairs function
  for FMU model inputs of causality `input`,
  which is consistent with the FMU model input of causality `parameter`.

## Version 2.0.0 (December 2023)

### Added

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
- [TimeSeries][gemseo_fmu.utils.time_series.TimeSeries]
  allows to specify inputs as time series.
- [gemseo-fmu.problems][gemseo_fmu.problems] contains use cases,
  either defined as [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  or simply as FMU files;
  use [get_fmu_file_path][gemseo_fmu.problems.fmu_files.get_fmu_file_path]
  to get a FMU file path easily.
- [DoStepFMUDiscipline][gemseo_fmu.disciplines.do_step_fmu_discipline.DoStepFMUDiscipline]
  is an [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  whose execution is only one time step ahead.
- [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
  is a system of static and time-stepping disciplines
  which executes them sequentially at each time step.

### Changed

- The [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  relies on the library [FMPy](https://github.com/CATIA-Systems/FMPy).
- [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  is in [gemseo-fmu.disciplines][gemseo_fmu.disciplines].

### Removed

Support for Python 3.8.

## Version 1.0.1 (June 2023)

Update to GEMSEO 5.

## Version 1.0.0 (January 2023)

First release.
