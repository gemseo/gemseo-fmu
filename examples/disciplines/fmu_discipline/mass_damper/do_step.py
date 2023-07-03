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
"""
Use do step
===========
"""
from __future__ import annotations

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from matplotlib import pyplot as plt

discipline = FMUDiscipline(
    get_fmu_file_path("Mass_Damper"),
    ["mass.m", "spring.c"],
    ["y"],
    initial_time=0.0,
    final_time=1.0,
    time_step=0.0001,
    do_step=True,
    restart=False,
)
for _ in range(1000):
    discipline.execute()
    plt.scatter(
        discipline.time,
        discipline.local_data["y"],
    )
plt.xlabel("Time [s]")
plt.ylabel("Amplitude [m]")
plt.show()
