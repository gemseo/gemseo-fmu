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
"""# Use time series

The input variables with `input` causality
as well as some input variables with `parameter` causality
can be set with time series.
"""

from __future__ import annotations

from matplotlib import pyplot as plt

from gemseo_fmu.disciplines.dynamic_fmu_discipline import DynamicFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from gemseo_fmu.utils.time_series import TimeSeries

# %%
# Let us create a discipline
# to simulate a mass damper defined in a FMU model
# from 0 to 1 second with a time step of 0.1 millisecond:
#
# ![ ](../../../../images/mass_damper.png)
#
# We only use the mass of the sliding mass [kg]
# and the spring constant [N/m] as inputs
# and the position of the mass [m] as output.
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
# we simulate the FMU with the default input values,
# and in particular a constant value for the mass:
discipline.execute()

# %%
# and store the time evolution of both its position and the mass:
default_y_evolution = discipline.local_data["y"]
default_mass = discipline.local_data["mass.m"]

# %%
# Then,
# we repeat the experiment with a custom time series for the mass,
# characterized by a sharp change after 0.5 seconds.
time_series = TimeSeries(time=[0.0, 0.25, 0.5, 1.0], observable=[4.0, 2.0, 0.2, 0.1])
discipline.execute({"mass.m": time_series})

# %%
# Lastly,
# we use a chart to compare the positions of the mass:
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
ax1.plot(discipline.time, default_y_evolution, label="Default")
p = ax1.plot(discipline.time, discipline.local_data["y"], label="Custom")
ax1.set_ylabel("Amplitude [m]")
ax1.legend()
ax2.axhline(default_mass, label="Default")
ax2.plot(
    discipline.time,
    discipline.local_data["mass.m"],
    label="Custom",
    color=p[0].get_color(),
)
ax2.set_ylabel("Mass [kg]")
plt.xlabel("Time [s]")
ax2.legend()
plt.show()
