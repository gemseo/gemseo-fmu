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
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or initial documentation
#        :author: Jorge CAMACHO CASERO
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""
FMU-based Sellar MDO use case
=============================
"""
import sys
from pathlib import Path

from gemseo.api import configure_logger
from gemseo.api import create_design_space
from gemseo.api import create_scenario

from problems.sellar import Sellar1
from problems.sellar import Sellar2
from problems.sellar import SellarSystem

configure_logger()

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform

# %%
# Create the disciplines
# ----------------------
# In this example we take the FMU files directly from the FMU gallery.
# The disciplines are defined as follows:
sellar_1 = Sellar1(FMU_DIR_PATH / "Sellar1.fmu", kind="CS")
sellar_2 = Sellar2(FMU_DIR_PATH / "Sellar2.fmu", kind="CS")
sellar_system = SellarSystem(FMU_DIR_PATH / "SellarSystem.fmu", kind="CS")

disciplines = [sellar_1, sellar_2, sellar_system]

# %%
# Create the design space
# -----------------------
design_space = create_design_space()
design_space.add_variable("x_local", size=1, l_b=0.0, u_b=10.0, value=1.0)
design_space.add_variable("x_shared_1", size=1, l_b=-10, u_b=10.0, value=4.0)
design_space.add_variable("x_shared_2", size=1, l_b=0.0, u_b=10.0, value=3.0)
design_space.add_variable("y_1", size=1, l_b=-100.0, u_b=100.0, value=1.0)
design_space.add_variable("y_2", size=1, l_b=-100.0, u_b=100.0, value=1.0)


# %%
# Create and execute the MDO scenario
# -------------------
scenario = create_scenario(disciplines, "MDF", "obj", design_space)
scenario.add_constraint("c_1", "ineq")
scenario.add_constraint("c_2", "ineq")
scenario.set_differentiation_method("finite_differences", 1e-6)
scenario.execute({"algo": "SLSQP", "max_iter": 15})

# %%
# Analyze the results
# -------------------
optimum = scenario.get_optimum()
print(optimum)
x_opt = scenario.design_space.get_current_value(as_dict=True)
print(x_opt)
scenario.post_process("OptHistoryView", show=True, save=False)
