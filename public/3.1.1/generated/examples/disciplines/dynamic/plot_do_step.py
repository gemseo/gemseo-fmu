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
"""# Use time stepping

The
[DoStepFMUDiscipline][gemseo_fmu.disciplines.do_step_fmu_discipline.DoStepFMUDiscipline]
can be used to simulate a co-simulation FMU model
by manually advancing one step at a time.
"""

from __future__ import annotations

from matplotlib import pyplot as plt

from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# Let us create a discipline
# to simulate a mass damper defined in an FMU model
# from 0 to 1 second with a time step of 0.1 millisecond:
#
# ![ ](../../../../images/mass_damper.png)
#
# We only use the mass of the sliding mass [kg]
# and the spring constant [N/m] as inputs.
# The position of the mass [m] is used as output.
discipline = DoStepFMUDiscipline(
    get_fmu_file_path("Mass_Damper"),
    ["mass.m", "spring.c"],
    ["y"],
    initial_time=0.0,
    final_time=1.0,
    time_step=0.0001,
)

# %%
# Then,
# we execute the discipline 10 times
# and create the graph as we go along with different point colors.
# In that case,
# executing the discipline 10 times
# means that we are advancing 10 times by one time step.
for _ in range(10):
    discipline.execute()
    plt.scatter(
        discipline.time,
        discipline.local_data["y"],
    )
plt.xlabel("Time [s]")
plt.ylabel("Amplitude [m]")
plt.show()

# %%
# !!! note
#     We can also do time stepping with
#     [DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
#     by setting `do_step` to `False` and `restart` to `False`.
