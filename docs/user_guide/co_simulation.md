<!--
 Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

 This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
 International License. To view a copy of this license, visit
 http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
 Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Co-simulation

A
[TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
is an
[MDODiscipline][gemseo.core.discipline.MDODiscipline]
defined by a system of static and time-stepping disciplines:

- a static discipline computes an output $y$ at time $t_k$
  from an input $x$ at time $t_k$, i.e. $y(t_k)=f(x(t_k))$,
- a time-stepping discipline computes an output $y$ at time $t_k$
  from an input $y$ at time $t_k$ and its state $s$ at time $t_k$,
  i.e. $y(t_k)=f(x(t_k),s(t_k),t_k)$.

At each time step $t_k$,
the
[TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
executes a collection of such disciplines using a co-simulation master algorithm
based on a multidisciplinary analysis (MDA).

## Basics

### Instantiation

The instantiation of a
[TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
only requires a list of disciplines, a final time and a time step:

```python
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.disciplines.dynamic_fmu_discipline import DynamicFMUDiscipline
from gemseo.disciplines.analytic import AnalyticDiscipline

disciplines = [
    "file_path.fmu",
    DynamicFMUDiscipline("other_file_path.fmu"),
    AnalyticDiscipline({"y":"2*x"})
]
system = TimeSteppingSystem(disciplines, 1, 0.1)
```

The disciplines can be either an FMU file path,
a static discipline or a dynamic discipline.

### Restart

By default,
an execution starts from the initial time.
Set `restart` to `False` if you want to restart from the initial time.

### Time stepping

By default,
an execution simulates from the initial time to the final time.
Set `do_step` to `True` if you want to simulate with only one time step.

### Time step

By default,
the time-stepping disciplines use the time step passed at instantiation.
Set `apply_time_step_to_disciplines` to `False`  if you want to use their specific time steps.

## Master algorithms

The master algorithm computes a coupling graph from the disciplines,
in order to identify the strong and weak coupling variables:

- two disciplines are strongly coupled if they are directly or indirectly interdependent,
- two disciplines are weakly if one does not take as input an output from the other.

!!! warning

    This identification based on input and output names
    implies a naming convention shared by all disciplines.

Then,
it executes the disciplines sequentially according to the coupling graph orientation
and solves the cycles, *i.e.* groups of strongly coupled disciplines, with an MDA algorithm.

!!! note

    For the moment,
    these MDA-based algorithms use a single iteration,
    as the rollback mechanism is not implemented

By default (`algo_name="MDAJacobi"`),
this algorithm is the Jacobi method,
which enables parallel execution.
One can also use the Gauss-Seidel method,
which is a serial approach;
initialize the
[TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
class with `algo_name="MDAGaussSeidel"` to use it.

!!! tip

    Use the dictionary `mda_options` to customize the MDA algorithm
    and subclass [BaseMDA][gemseo.mda.base_mda.BaseMDA] to create a new master algorithm.
