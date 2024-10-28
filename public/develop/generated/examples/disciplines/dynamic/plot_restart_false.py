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
"""# Do not restart

In some situations,
we may want to configure the
[DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
so that each execution starts where the previous one stopped.
"""

from __future__ import annotations

from matplotlib import pyplot as plt

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
    restart=False,
)
# %%
# !!! note
#     We had to set `restart` to `False`
#     as the default behavior of the
#     [DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
#     is to run each execution from the start time.
#
# Then,
# we execute the discipline setting a simulation time of 0.3 seconds
# with the default input values:
discipline.set_next_execution(simulation_time=0.3)
discipline.execute()

# %%
# and store the time evolution of the position of the mass:
time_evolution_1 = (discipline.time, discipline.local_data["y"])

# %%
# We repeat this experiment with custom input values:
discipline.set_next_execution(simulation_time=0.3)
discipline.execute({"mass.m": 1.5, "spring.c": 1050.0})

# %%
# store the results:
time_evolution_2 = (discipline.time, discipline.local_data["y"])

# %%
# and execute the discipline until the final time:
discipline.execute()
time_evolution_3 = (discipline.time, discipline.local_data["y"])

# %%
# Lastly,
# we draw this trajectory on a chart:
plt.plot(*time_evolution_1, label="Default 1/3")
plt.plot(*time_evolution_2, label="Default 2/3")
plt.plot(*time_evolution_3, label="Default 3/3")
plt.xlabel("Time [s]")
plt.ylabel("Amplitude [m]")
plt.legend()
plt.show()
