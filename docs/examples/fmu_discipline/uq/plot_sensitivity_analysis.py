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
"""# Comparing sensitivity indices.

The
[FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
can also be used with static models
to run a sensitivity analysis, for example.
"""
from __future__ import annotations

from gemseo.algos.parameter_space import ParameterSpace
from gemseo.uncertainty.sensitivity.morris.analysis import MorrisAnalysis
from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from numpy import pi

# %%
# In this example,
# we consider the Ishigami function
#
# $$Y=\sin(X_1)+7\sin(X_2)^2+0.1*X_3^4\sin(X_1)$$
#
# whose description is contained in the FMU file created from the Modelica code below:
#
# ``` bash
#     model IshigamiFunction
#       parameter Real x1 = 0;
#       parameter Real x2 = 0;
#       parameter Real x3 = 0;
#       output Real y;
#     equation
#       y = sin(x1) + 7 * sin(x2)^2 + 0.1 * x3^4 * sin(x1);
#     end IshigamiFunction;
# ```
#
discipline = StaticFMUDiscipline(get_fmu_file_path("IshigamiFunction"))

# %%
# The different uncertain variables $X_1$ , $X_2$ and $X_3$
# are independent and identically distributed
# according to the uniform distribution between $-\pi$ and $\pi$:
uncertain_space = ParameterSpace()
for variable in ["x1", "x2", "x3"]:
    uncertain_space.add_random_variable(
        variable, "SPUniformDistribution", minimum=-pi, maximum=pi
    )

# %%
# We create a
# [MorrisAnalysis][gemseo.uncertainty.sensitivity.morris.analysis.MorrisAnalysis]
# and compute the sensitivity indices:
morris_analysis = MorrisAnalysis([discipline], uncertain_space, None)
morris_analysis.compute_indices()

# %%
# Lastly, we compare these analyses using a bar chart:
morris_analysis.plot("y", save=False, show=True)
