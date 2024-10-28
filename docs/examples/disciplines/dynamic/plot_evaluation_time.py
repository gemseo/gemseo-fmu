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
"""# Set evaluation time

Instead of simulating an FMU model
from an initial time to a final time
in one go,
we may want to simulate it
time window by time window.

The
[DynamicFMUDiscipline][gemseo_fmu.disciplines.dynamic_fmu_discipline.DynamicFMUDiscipline]
makes this possible.
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
)

# %%
# Firstly,
# we execute the discipline setting a simulation time of 0.3 seconds
# with the default input values:
discipline.set_next_execution(simulation_time=0.3)
discipline.execute()

# %%
# and store the results:
default_1 = (discipline.time, discipline.local_data["y"])

# %%
# Then,
# we repeat the experiment until the final time:
discipline.set_next_execution(restart=False)
discipline.execute()

# %%
# and store the results:
default_2 = (discipline.time, discipline.local_data["y"])

# %%
# Thirdly,
# we restart the discipline (default setting)
# and execute the discipline setting a simulation time of 0.3 seconds
# with custom input values:
discipline.set_next_execution(simulation_time=0.3)
discipline.execute({"mass.m": 1.5, "spring.c": 1050.0})

# %%
# and store the results:
custom_1 = (discipline.time, discipline.local_data["y"])

# %%
# Then,
# we repeat the experiment until the final time
# with the same custom input values:
discipline.set_next_execution(restart=False)
discipline.execute({"mass.m": 1.5, "spring.c": 1050.0})

# %%
# and store the results:
custom_2 = (discipline.time, discipline.local_data["y"])

# %%
# Lastly,
# we use a chart
# to compare the default and custom results:
plt.plot(*default_1, label="Default 1/2")
plt.plot(*default_2, label="Default 2/2")
plt.plot(*custom_1, label="Custom 1/2")
plt.plot(*custom_2, label="Custom 2/2")
plt.xlabel("Time [s]")
plt.ylabel("Amplitude [m]")
plt.legend()
plt.show()
