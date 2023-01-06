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
Create a discipline for the Sellar problem from a FMU file and computes its jacobians
==========================================
"""
import sys
from pathlib import Path

from problems.sellar import Sellar1
from problems.sellar import Sellar2
from problems.sellar import SellarSystem

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform


# Step 1: create the disciplines (with jacobians specific to the Sellar problem)
# In this example we take a FMU files directly from the FMU gallery
disc_sellar_1 = Sellar1(FMU_DIR_PATH / "Sellar1.fmu", kind="CS")
disc_sellar_2 = Sellar2(FMU_DIR_PATH / "Sellar2.fmu", kind="CS")
disc_sellar_system = SellarSystem(FMU_DIR_PATH / "SellarSystem.fmu", kind="CS")

disciplines = [disc_sellar_1, disc_sellar_2, disc_sellar_system]

# Step 2: execute the disciplines
disc_sellar_1.execute()
disc_sellar_2.execute()
disc_sellar_system.execute()

# Step 3: compute the jacobians
disc_sellar_1._compute_jacobian()
disc_sellar_2._compute_jacobian()
disc_sellar_system._compute_jacobian()

# Step 4: access the jacobians
print(dict(disc_sellar_1.jac))
print(dict(disc_sellar_2.jac))
print(dict(disc_sellar_system.jac))
