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
is a
[Discipline][gemseo.core.discipline.discipline.Discipline]
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

    GEMSEO provides facilities for renaming the input and output variables of a set of disciplines,
    which are illustrated
    [in this example](https://gemseo.readthedocs.io/en/stable/examples/disciplines/variables/plot_variable_renaming.html).
    In the specific case of FMU disciplines,
    the instantiation argument `variable_names` can be set to a
    [VariableRenamer.translators][gemseo.utils.variable_renaming.VariableRenamer.translators].

Then,
it executes the disciplines sequentially according to the coupling graph orientation
and solves the cycles, *i.e.* groups of strongly coupled disciplines, with an MDA algorithm.

!!! warning

    For the moment,
    the rollback mechanism for re-simulating from previous time to current time is not implemented,
    which prevents these algorithms from iterating at any time
    (see the sections Jacobi and Gauss-Seidel algorithms below for more information).

    However,
    at initial time, and at this time only,
    the MDA algorithm can iterate
    if the user sets the ``max_mda_iter_at_t0`` argument to the maximum number of iterations of the MDA algorithm
    (default: no iteration at initial time).
    This can be used to obtain multidisciplinary feasible initial conditions,
    in the case where the disciplines have inconsistent initial conditions.

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

In the following,
we explain the mechanics of the Jacobi and Gauss-Seidel algorithms.

### Jacobi algorithm

At initial time $t^0$,
this master algorithm initializes the state variables of the disciplines with common values.
Then,
the disciplines are executed separately,
which corresponds to a simulation from time $t^0$ to time $t^1$.
If the difference in state variable values between the two times is significant
and the rollback mechanism is implemented,
we return to time $t^0$ and repeat the time integration from time $t^0$ to time $t^1$
until convergence or budget exhaustion.
Lastly,
we repeat this process from time $t^1$ to time $t^2$, from time $t^2$ to time $t^3$ and so on until final time.

This master algorithm is called _Jacobi algorithm_
because of its structural similarity with the [Jacobi method](https://en.wikipedia.org/wiki/Jacobi_method)
used in numerical linear algebra.
As the disciplines are executed separately,
these executions can be parallelized
and the algorithm is then qualified as parallel.

Here is an illustration from time $t^n$ to time $t^{n+2}$
in the case of two strongly coupled disciplines
with a budget of two iterations:

<figure markdown="span">
  ![Jacobi algorithm](https://upload.wikimedia.org/wikipedia/en/thumb/f/fa/Jacobi_iteration_sequence_for_two_subsystems.pdf/page1-708px-Jacobi_iteration_sequence_for_two_subsystems.pdf.jpg)
  <figcaption>Jacobi iteration sequence for two disciplines, by <a href="https://en.wikipedia.org/wiki/File:Jacobi_iteration_sequence_for_two_subsystems.pdf">Ssicklinger / wikipedia</a>, <a href="https://creativecommons.org/licenses/by-sa/3.0/deed.en">CC BY-SA 3.0</a>.</figcaption>
</figure>

### Gauss-Seidel algorithm

At initial time $t^0$,
this master algorithm initializes the state variables of the disciplines separately.
Then,
the disciplines are executed sequentially,
which corresponds to a simulation from time $t^0$ to time $t^1$.
If the difference in state variable values between the two times is significant
and the rollback mechanism is implemented,
we return to time $t^0$ and repeat the time integration from time $t^0$ to time $t^1$
until convergence or budget exhaustion.
Lastly,
we repeat this process from time $t^1$ to time $t^2$, from time $t^2$ to time $t^3$ and so on until final time.

!!! note

    The results depends on the order of the disciplines,
    which are executed sequentially,
    especially when they are poorly converged.

This master algorithm is called _Gauss-Seidel algorithm_
because of its structural similarity with the [Gauss-Seidel method](https://en.wikipedia.org/wiki/Gauss-Seidel_method)
used in numerical linear algebra.
As the disciplines are executed sequentially,
these executions cannot be parallelized
and the algorithm is then qualified as serial.

Here is an illustration from time $t^n$ to time $t^{n+2}$
in the case of two strongly coupled disciplines
with a budget of two iterations:

<figure markdown="span">
  ![Gauss-Seidel algorithm](https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Gauss-Seidel_iteration_sequence_for_two_subsystems.pdf/page1-708px-Gauss-Seidel_iteration_sequence_for_two_subsystems.pdf.jpg)
  <figcaption>Gauss-Seidel iteration sequence for two disciplines, by <a href="https://en.wikipedia.org/wiki/File:Gauss-Seidel_iteration_sequence_for_two_subsystems.pdf">Ssicklinger / wikipedia</a>, <a href="https://creativecommons.org/licenses/by-sa/3.0/deed.en">CC BY-SA 3.0</a>.</figcaption>
</figure>
