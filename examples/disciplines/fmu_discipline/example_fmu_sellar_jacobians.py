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
Create a discipline for the Sellar problem from a FMU file and computes its Jacobians
=====================================================================================
"""
from __future__ import annotations

from gemseo_fmu.problems.disciplines.sellar.sellar_1 import FMUSellar1
from gemseo_fmu.problems.disciplines.sellar.sellar_2 import FMUSellar2
from gemseo_fmu.problems.disciplines.sellar.sellar_system import FMUSellarSystem


# %%
# Step 1: create the disciplines (with Jacobians specific to the Sellar problem)
# In this example we take a FMU files directly from the FMU gallery
sellar_1 = FMUSellar1()
sellar_2 = FMUSellar2()
sellar_system = FMUSellarSystem()
disciplines = [sellar_1, sellar_2, sellar_system]

# %%
# Step 2: execute the disciplines
sellar_1.execute()
sellar_2.execute()
sellar_system.execute()
print(sellar_1.get_output_data())
print(sellar_2.get_output_data())
print(sellar_system.get_output_data())

# %%
# Step 3: compute the Jacobians
sellar_1.linearize(compute_all_jacobians=True)
sellar_2.linearize(compute_all_jacobians=True)
sellar_system.linearize(compute_all_jacobians=True)

# %%
# Step 4: access the Jacobians
print(sellar_1.jac)
print(sellar_2.jac)
print(sellar_system.jac)
