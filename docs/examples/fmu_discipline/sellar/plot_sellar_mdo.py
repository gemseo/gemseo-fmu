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
"""# FMU-based Sellar MDO use case

The
[FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
can also be used with static models
to solve an MDO problem, for example.
"""
from __future__ import annotations

from gemseo import configure_logger
from gemseo import create_design_space
from gemseo import create_scenario
from gemseo_fmu.problems.disciplines.sellar.sellar_1 import FMUSellar1
from gemseo_fmu.problems.disciplines.sellar.sellar_2 import FMUSellar2
from gemseo_fmu.problems.disciplines.sellar.sellar_system import FMUSellarSystem

configure_logger()

# %%
# Let us consider the Sellar problem.
#
# Firstly,
# we instantiate the disciplines:
disciplines = [FMUSellar1(), FMUSellar2(), FMUSellarSystem()]

# %%
# Then
# we create the design space:
design_space = create_design_space()
design_space.add_variable("x_local", size=1, l_b=0.0, u_b=10.0, value=1.0)
design_space.add_variable("x_shared_1", size=1, l_b=-10, u_b=10.0, value=4.0)
design_space.add_variable("x_shared_2", size=1, l_b=0.0, u_b=10.0, value=3.0)
design_space.add_variable("y_1", size=1, l_b=-100.0, u_b=100.0, value=1.0)
design_space.add_variable("y_2", size=1, l_b=-100.0, u_b=100.0, value=1.0)


# %%
# Thirdly,
# we create and execute the MDO scenario:
scenario = create_scenario(disciplines, "MDF", "obj", design_space)
scenario.add_constraint("c_1", "ineq")
scenario.add_constraint("c_2", "ineq")
scenario.execute({"algo": "SLSQP", "max_iter": 15})

# %%
# Lastly,
# we display the optimization history:
scenario.post_process("OptHistoryView", show=True, save=False)
