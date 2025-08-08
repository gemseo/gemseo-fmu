<!--
 Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

 This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
 International License. To view a copy of this license, visit
 http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
 Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# FMU discipline

The [functional mock-up interface (FMI)](https://fmi-standard.org/)
is a popular free standard to exchange dynamic simulation models.
This standard defines the notion of functional mock-up unit (FMU)
through a ZIP file containg a mix of XML files, binaries and C code.
GEMSEO-FMU proposes
new types of [Discipline][gemseo.core.discipline.discipline.Discipline]
to simulate an FMU model:

- the [StaticFMUDiscipline][gemseo_fmu.disciplines.static_fmu_discipline.StaticFMUDiscipline]
  to simulate a time-independent FMU model $f$
  like $y=f(x)$
  where $x$ is the input and $y$ is the output,
- the [DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
  to simulate a time-dependent FMU model $f$
  like $y(t_k)=f(y(t_{k-1}),x(t_{k-1}),\Delta t_k)$
  where $t_{k-1}$ is the previous time,
  $t_k$ is the current time
  and $\Delta t_k=t_k-t_{k-1}$ is the time step,
- the [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  to simulate a time-independent or time-dependent FMU model $f$
  like $y=f(x)$ or $y(t_k)=f(y(t_{k-1}),x(t_{k-1}),\Delta t_k)$.

!!! info
    [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
    is an alias of [DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
    and can be used to simulate both time-dependent and time-independent FMU models.
    Most of the time,
    the FMU model are dynamic and so this naming shortcut can be useful.

    !!! note
        `gemseo-fmu` distinguishes between static and dynamic models
        to facilitate use by newcomers in the FMI standard.
        However,
        it should be noted that an FMU model does not make this distinction:
        all FMU models include the notion of time.
        Thus,
        a model summing two operands $a$ and $b$ can be run
        with different time steps and different final times;
        it will then produce the same result $c=a+b$ at each time step.

In the following,
we will talk about the
[FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline].
The content would be the same for
[StaticFMUDiscipline][gemseo_fmu.disciplines.static_fmu_discipline.StaticFMUDiscipline]
except for the parts related to the notion of time,
which are specific to the
[DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline].
You will find examples of both
[StaticFMUDiscipline][gemseo_fmu.disciplines.static_fmu_discipline.StaticFMUDiscipline]
and
[DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline].
in the galleries of examples.

## Basics

As any [Discipline][gemseo.core.discipline.discipline.Discipline],
you mainly need to know
how to instantiate an
[FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline],
and how to execute it.
Advanced features will be presented later.

### Instantiation

The only mandatory argument is the path to the FMU file:

``` py
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline

discipline = FMUDiscipline("my_model.fmu")
```

#### Inputs

When `input_names` is `()` (default),
the input variables of the discipline are
all the variables of the FMU model with type _input_ or _parameter_.

When `input_names=None`,
the discipline has no input variables.

The input variables can be a subset
of the inputs and parameters of the FMU model
by using `input_names=some_input_names`.

#### Outputs

When `ouput_names` is `()` (default),
the output variables of the discipline are
all the outputs of the FMU model
plus the time.

The time can be excluded from the outputs
with `add_time_to_output_grammar=False`.

The output variables can be a subset
of the outputs of the FMU model
by using `output_names=some_output_names`.

#### Renaming inputs and outputs

Sometimes the names of variables in the FMU model are not meaningful,
or are used by other FMU models in the same study to represent another quantity.
In both cases,
we might want to use discipline variable names that are different from those in the FMU model.
That's what argument `variable_names` is for.
This dictionary of the form `{fmu_model_variable_name: discipline_variable_name, ...}`
defines the mapping between the variable names in the FMU model that do not suit us
and the variable names that we want to use in the discipline.

#### Time settings

Regarding the time settings,
this minimal instantiation implies that
each execution of the discipline will execute the FMU model
as co-simulation FMU model
from its start time to its final time
with a default time step
and a default solver for ordinary differential equation (ODE).
If the start time is not defined in the FMU models,
this is set to 0.
If the final time is not defined in the FMU models,
this time is set to the start time,
and it is therefore advisable to use a custom value.

The time step and the solver can be changed
with the float argument `time_step` and the string argument `solver_name`.

An execution can also advance a single time step from the start time
by using `do_step=True`.
When using both `do_step=True` and `restart=False`,
an execution advances a single time step from the previous one.

!!! info
    The [DoStepFMUDiscipline][gemseo_fmu.disciplines.do_step_fmu_discipline.DoStepFMUDiscipline]
    is an [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
    whose execution advances a single time step from the previous time.
    It can be useful if you want
    an [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
    doing time stepping throughout its life cycle.

Lastly,
the final time can be changed with the float argument `final_time`.

!!! warning
    The discipline cannot be executed after the final time.

### Execution

An [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
can be easily executed with the default values of its inputs:

``` py
discipline.execute()
```

or with custom ones passed as a dictionary:

``` py
discipline.execute({"my_input": my_input_value})
```

## Advanced

### Time series

An input value can be either a scalar
or a [TimeSeries][gemseo_fmu.disciplines.time_series.TimeSeries].

For instance,
a discipline can take as input a signal $x(t)$
known at time steps $t_1,t2,\ldots,t_N$:

``` py
from gemseo.disciplines.time_series import TimeSeries

my_time_series = TimeSeries([t1, t2, ..., tN], [x1, x2, ..., xN])
```

The values of the time $t$ and observable $x$
can be easily accessed:

``` py
t = my_time_series.time
x = my_time_series.observable
```

In practice,
you can use it
either to set the default inputs:

``` py
discipline.default_inputs["my_input"] = my_time_series
```

or to execute the discipline:

``` py
discipline.execute({"my_input": my_time_series})
```

### Configure the next execution

The time settings of the next execution of the discipline
depends on the time settings defined at instantiation
but can be changed temporarily.

[set_next_execution()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.set_next_execution]
allows to
change the duration of the simulation associated to the next execution,
change the time step used during the next execution
and restart the discipline instantiated with `restart=False`
(and vice-versa).

!!! warning "Only the next execution"
    This method only applies to the next execution.
    It must be used
    each time a different behavior from the instantiation settings is required.

!!! warning "Simulation time"
    The simulation time must be
    less than or equal to the time remaining before the final time.

Here is an example of how to use this method:

``` py
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline

# Create a discipline from an FMU model:
# - set the final time at 12 seconds,
# - start an execution at the time step where the previous one stopped.
discipline = FMUDiscipline("my_model.fmu", final_time=12, restart=False)

# Simulate with the default values of the inputs during 3 seconds
discipline.set_next_execution(simulation_time=3)
discipline.execute()

# Simulate with custom values of the inputs during 2 seconds
discipline.set_next_execution(simulation_time=2)
discipline.execute({"x": array([12.3])})

# Simulate with custome values until final time (i.e. during 7 seconds)
discipline.execute({"x": array([16.8])})
```

### Restart

The argument `restart` has already been introduced in this page.

It can also be used to compare trajectories:

``` py
import matplotlib.pyplot as plt
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline

discipline = FMUDiscipline("my_model.fmu")
discipline.execute()
default_trajectory = discipline.local_data["y"]

discipline.execute({"x": array([12.3])})
first_custom_trajectory = discipline.local_data["y"]

discipline.execute({"x": array([16.8])})
second_custom_trajectory = discipline.local_data["y"]

time = discipline.local_data["time"]

plt.plot(time, default_trajectory, label="Default")
plt.plot(time, first_custom_trajectory, label="Option 1")
plt.plot(time, second_custom_trajectory, label="Option 2")
plt.show()
```
