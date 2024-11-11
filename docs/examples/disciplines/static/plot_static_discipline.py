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
"""# Static discipline

The
[StaticFMUDiscipline][gemseo_fmu.disciplines.static_fmu_discipline.StaticFMUDiscipline]
can be used to simulate a time-independent FMU model.
"""

from __future__ import annotations

from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

# %%
# Let us create a discipline based on an FMU model
# computing the output $y$ from the inputs $u_1$ and $u_2$
# as $y=f(u_1,u_2)=k_1u_1+k_2u_2$:
discipline = StaticFMUDiscipline(get_fmu_file_path("add"))

# %%
# We can have a look to the default inputs:
discipline.default_input_data

# %%
# and see that they are equal to zero.
# We can also see that $k_1$ and $k_2$ are discipline inputs
# in the same way as $u_1$ and $u_2$.
# However,
# their causality is _parameter_
# while the causality of $u_1$ and $u_2$ is _input_:
discipline.causalities_to_variable_names

# %%
# Then,
# we can execute the discipline with the default input values
discipline.execute()
discipline.get_output_data()

# %%
# and check that the output is equal to 0 as expected.
# Then,
# we can execute this discipline with new input values:
discipline.execute({"u1": 2.0, "u2": 3.0})
discipline.get_output_data()

# %%
# and check that the output is equal to 5 as expected.
# Lastly,
# we can also change the values of the inputs with _parameter_ causality:
discipline.execute({"u1": 2.0, "u2": 3.0, "add.k1": 4.0})
discipline.get_output_data()

# %%
# The output is equal to 11 as expected.
