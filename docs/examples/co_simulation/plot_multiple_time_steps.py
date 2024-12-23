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
"""# Co-simulation with multiple time steps

Sometimes,
we may want to simulate a system of several FMU models coupled together.
[TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem]
allows to perform this _co-simulation_ task,
even in the presence of FMU models with variable time steps.
"""

from __future__ import annotations

from matplotlib import pyplot as plt

from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# Let us consider a set of two mass-spring pairs connected to each other
# and modelled by two FMU models:
#
# $$
# \begin{cases}
# x_1' = v_1\\
# v_1' = -\frac{k_1+k_2}{m_1}x_1+\frac{k_2}{m_1}x_2
# \end{cases}
# $$
#
# and
#
# $$
# \begin{cases}
# x_2' = v_2\\
# v_2' = -\frac{k_2+k_3}{m_2}x_2+\frac{k_2}{m_2}x_1
# \end{cases}
# $$
#
# These models can be modeled using the
# [DoStepFMUDiscipline][gemseo_fmu.disciplines.do_step_fmu_discipline.DoStepFMUDiscipline]
# class.
# For illustration purposes,
# we use different time steps for these models:
sub_system_1 = DoStepFMUDiscipline(
    get_fmu_file_path("MassSpringSubSystem1"), time_step=0.004
)
sub_system_2 = DoStepFMUDiscipline(
    get_fmu_file_path("MassSpringSubSystem2"), time_step=0.01
)
# %%
# !!! note
#     There is no need for one time step to be a multiple of the other.
#
# Then, these disciplines can be co-simulated by instantiating a
# [TimeSteppingSystem][gemseo_fmu.disciplines.time_stepping_system.TimeSteppingSystem].
system = TimeSteppingSystem(
    (sub_system_1, sub_system_2), 50, 0.01, apply_time_step_to_disciplines=False
)

# %%
# and executing it from initial time to final time:
system.execute()

# %%
# or with time stepping by setting `do_step` to `False` at instantiation.
#
# !!! note
#     We set `apply_time_step_to_disciplines` to `False` at instantiation
#     in order to let the disciplines use their own time steps.
#     By default,
#     the global time step passed at instantiation (0.1 in this example)
#     is used by the disciplines.
#
# For this particular example,
# we also have a FMU model of the complete system:
reference = FMUDiscipline(
    get_fmu_file_path("MassSpringSystem"), final_time=50, time_step=0.01
)
reference.execute()

# %%
# Then,
# we can compare the solutions graphically
# in terms of position and velocity of the two masses
# and note that for this example,
# the co-simulation of the two subsystems is equivalent
# to that of the complete system.

fig, (ax1, ax2) = plt.subplots(2, 1)
time_1 = system.local_data["MassSpringSubSystem1:time"]
time_2 = system.local_data["MassSpringSubSystem2:time"]
ax1.plot(time_1, system.local_data["x1"], label="x1", color="red")
ax1.plot(time_2, system.local_data["x2"], label="x2", color="blue")
ax2.plot(time_1, system.local_data["v1"], label="v1", color="red")
ax2.plot(time_2, system.local_data["v2"], label="v2", color="blue")

time = reference.local_data["MassSpringSystem:time"]
ax1.plot(time, reference.local_data["x1"], label="x1[ref]", linestyle="--", color="red")
ax1.plot(
    time, reference.local_data["x2"], label="x2[ref]", linestyle="--", color="blue"
)
ax2.plot(time, reference.local_data["v1"], label="v1[ref]", linestyle="--", color="red")
ax2.plot(
    time, reference.local_data["v2"], label="v2[ref]", linestyle="--", color="blue"
)

ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Position (m)")
ax1.grid()
ax1.legend()
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Velocity (m/s)")
ax2.grid()
ax2.legend()
plt.show()
