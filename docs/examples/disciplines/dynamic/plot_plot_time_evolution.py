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
"""# Plot a time evolution

The time evolution of a discipline output can easily be plotted,
using the
[FMUDiscipline.plot][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.plot]
method.
"""

from __future__ import annotations

from gemseo_fmu.disciplines.dynamic_fmu_discipline import DynamicFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# Let us create a discipline
# to simulate a mass damper defined in an FMU model
# from 0 to 1 second with a time step of 0.1 milliseconds:
#
# ![ ](../../../../images/mass_damper.png)
#
# We only use the mass of the sliding mass [kg]
# and the spring constant [N/m] as inputs.
# The position of the mass [m] is used as output.
discipline = DynamicFMUDiscipline(
    get_fmu_file_path("Mass_Damper"),
    ["mass.m", "spring.c"],
    ["y"],
    initial_time=0.0,
    final_time=1.0,
    time_step=0.0001,
)

# %%
# Firstly,
# we execute the discipline:
discipline.execute()

# %%
# Then,
# we can easily access the local data, *e.g* the output `"y"`:
discipline.local_data["y"]

# %%
# But it is not very easy to read
# and plotting the time evolution of this variable is a better option:
discipline.plot("y", save=False, show=True)

# %%
# We can also restrict the view to a specific time window
# defined by the start time index:
discipline.plot("y", time_window=3000, save=False, show=True)

# %%
# or both the start and end time indices:
discipline.plot("y", time_window=[3000, 7000], save=False, show=True)
