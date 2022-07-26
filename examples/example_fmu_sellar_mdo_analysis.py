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
Short example illustrating the MDO Sellar problem based on disciplines extracted from
a FMU file
==========================================
"""
from gemseo.api import create_design_space
from gemseo.api import create_scenario
from numpy import array
from numpy import ones

from problems.sellar import Sellar1
from problems.sellar import Sellar2
from problems.sellar import SellarSystem

# Step 1: create the disciplines
sellar_1 = Sellar1("../fmu_files/SellarDis1.fmu", kind="CS")
sellar_2 = Sellar2("../fmu_files/SellarDis2.fmu", kind="CS")
sellar_system = SellarSystem("../fmu_files/SellarSystem.fmu", kind="CS")

disciplines = [sellar_1, sellar_2, sellar_system]

# Step 2: create the design space
design_space = create_design_space()
design_space.add_variable("x_local", 1, l_b=0.0, u_b=10.0, value=ones(1))
design_space.add_variable("x_shared_1", 1, l_b=-10, u_b=10.0, value=array([4.0]))
design_space.add_variable("x_shared_2", 1, l_b=0.0, u_b=10.0, value=array([3.0]))
design_space.add_variable("y_1", 1, l_b=-100.0, u_b=100.0, value=ones(1))
design_space.add_variable("y_2", 1, l_b=-100.0, u_b=100.0, value=ones(1))

# Step 3: create and solve the MDO scenario
scenario = create_scenario(
    disciplines, "MDF", objective_name="obj", design_space=design_space
)
scenario.add_constraint("c_1", "ineq")
scenario.add_constraint("c_2", "ineq")
scenario.set_differentiation_method("finite_differences", 1e-6)
scenario.default_inputs = {"max_iter": 15, "algo": "SLSQP"}
scenario.execute()

optimum = scenario.get_optimum()
print(optimum)
x_opt = scenario.design_space.get_current_x_dict()
print(x_opt)

# Step 4: analyze the results
scenario.post_process("OptHistoryView", show=True, save=True)
