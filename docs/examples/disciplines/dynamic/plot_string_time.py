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
"""# Time as a character string

Time information can often be specified either in seconds or as a string written in
natural language, e.g. `"2h 34m 1s"` or `"2 hours, 34 minutes and 1 second"` (units
include y, m, w, d, h, min, s, ms).
"""

from __future__ import annotations

from matplotlib import pyplot as plt

from gemseo_fmu.disciplines.dynamic_fmu_discipline import DynamicFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# Let us create and use a discipline
# to simulate a mass damper defined in a FMU model
# from 0 to 1 second with a time step of 0.1 millisecond:
#
# ![ ](../../../../images/mass_damper.png)
#
# Here,
# we express the final time and time step in natural language
# with `"1 second"` and `"0.1ms"` instead of `1` and `0.0001`.
discipline = DynamicFMUDiscipline(
    get_fmu_file_path("Mass_Damper"),
    ["mass.m", "spring.c"],
    ["y"],
    initial_time=0.0,
    final_time="1 second",
    time_step="0.1ms",
)
discipline.execute()

# %%
# We can plot the time-evolution of the position of the mass:
# TODO(bump-gemseo): local_data is deprecated and returns a copy of the input and output data, so setting, updating or removing an item through it has no effect, and an output that _run produces through it is missing, even when produced by changing an input in place; return the outputs from _run or write them to output_data (or io.update_output_data(data)), write the inputs to input_data, and read input_data, output_data or io.get_merged_data()  # noqa: E501
plt.plot(discipline.time, discipline.local_data["y"])
plt.xlabel("Time [s]")
plt.ylabel("Amplitude [m]")
plt.show()
