# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This work is licensed under a BSD 0-Clause License.
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""# Co-simulation from multidisciplinary feasible initial conditions"""

from numpy import array

from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# ## The problem
#
# When co-simulating several FMU models,
# the latter do not always have consistent initial conditions,
# which can complicate the running of the master algorithm
# and result in erroneous variable evolutions over time.
#
# In this example,
# we will see how to update these initial conditions
# to make them multidisciplinary feasible.
# For that,
# we consider a very simple example:
#
# - a discipline A
#   computes $x(t) = x(t-1) + 1$ at $t>0$
#   with the initial equation $x(0) = 3 + y(0)$
#   and the initial condition $x(0) = 1$,
# - a discipline B computes $y(t) = y(t-1) + 2$ at $t>0$
#   with the initial equation $y(0) = 3 + 2x(0)$
#   and the initial condition $y(0) = 1$.
#
# So,
# after initialization,
# the output of A is incremented by 1 at each execution,
# while the output of B is incremented by 2.
#
# These disciplines are very similar,
# differing only in terms of increment and initial conditions.
# For this reason,
# they are implemented from the same FMU model,
# whose variables are renamed:
a = StaticFMUDiscipline(
    get_fmu_file_path("FMU3Model"),
    variable_names={"input": "y", "output": "x", "increment": "inc_a"},
    name="A",
)
b = StaticFMUDiscipline(
    get_fmu_file_path("FMU3Model"),
    variable_names={"input": "x", "output": "y", "increment": "inc_b"},
    name="B",
)
b.default_input_data["inc_b"] = array([2.0])

# %%
# ## The wrong way
#
# First,
# we can co-simulate these disciplines with the current initial conditions
# without iterating the master algorithm at initial time:
system = TimeSteppingSystem(
    (a, b),
    3,
    1,
)
_ = system.execute()
# %%
# and note the time evolutions of the output variables after three time steps:
{name: system.io.data[name] for name in ["x", "y"]}

# %%
# ## The right way
#
# Then,
# we can co-simulate these disciplines,
# by applying the default master algorithm at initial time:
system = TimeSteppingSystem(
    (a, b),
    3,
    1,
    mda_max_iter_at_t0=10,
)
_ = system.execute()
# %%
# and see that
# the time evolutions of the output variables after three time steps have changed:
{name: system.io.data[name] for name in ["x", "y"]}

# %%
# ## The difference
#
# This difference can be explained by the fact that
# the master algorithm has corrected the initial conditions,
# which were inconsistent.
#
# Indeed,
# the statement said that $x(0) = 1$ and $y(0) = 3 + 2x(0)$.
# Then, $y(0) = 5$.
# But the statement said also that $y(0) = 1$,
# which is contradictory!
#
# Now,
# let us consider the initial equation system
#
# $$\left\{\begin{matrix}x(0) = 3 + y(0)\\ y(0) = 3 + 2x(0)\end{matrix}\right.$$
#
# Its analytical solution is $(x(0),y(0)) = (-6,-9)$.
# This is what the master algorithm found numerically,
# before the three time steps increment these values.
#
# ## The take-home message
#
# When models have potentially inconsistent initial conditions,
# it may be prudent to
# perform a few iterations of the master algorithm at the initial time
# to ensure that the initial conditions are multidisciplinary feasible.
# To do this, fill in the argument `mda_max_iter_at_t0` of the
# [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem].
