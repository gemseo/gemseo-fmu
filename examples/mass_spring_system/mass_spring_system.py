# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""A system of masses and springs."""

from __future__ import annotations

from matplotlib import pyplot as plt

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

discipline = FMUDiscipline(
    get_fmu_file_path("MassSpringSystem"), final_time=50, time_step=0.01
)
discipline.execute()

fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.plot(discipline.local_data["x1"], label="x1[ref]", linestyle="--", color="red")
ax1.plot(discipline.local_data["x2"], label="x2[ref]", linestyle="--", color="blue")
ax2.plot(discipline.local_data["v1"], label="v1[ref]", linestyle="--", color="red")
ax2.plot(discipline.local_data["v2"], label="v2[ref]", linestyle="--", color="blue")

discipline = TimeSteppingSystem(
    (
        get_fmu_file_path("MassSpringSubSystem1"),
        get_fmu_file_path("MassSpringSubSystem2"),
    ),
    final_time=50,
    time_step=0.01,
)
discipline.execute()

ax1.plot(discipline.local_data["x1"], label="x1", color="red")
ax1.plot(discipline.local_data["x2"], label="x2", color="blue")
ax2.plot(discipline.local_data["v1"], label="v1", color="red")
ax2.plot(discipline.local_data["v2"], label="v2", color="blue")

ax1.grid()
ax1.legend()
ax2.grid()
ax2.legend()
plt.show()