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
from gemseo.api import configure_logger

from problems.sellar import Sellar1
from problems.sellar import Sellar2
from problems.sellar import SellarSystem

configure_logger()

# Step 1: create the disciplines (with jacobians specific to the Sellar problem)
sellar1_file = "../fmu_files/SellarDis1.fmu"
sellar2_file = "../fmu_files/SellarDis2.fmu"
sellar_system_file = "../fmu_files/SellarSystem.fmu"

disc_sellar_1 = Sellar1(sellar1_file, kind="CS")
disc_sellar_2 = Sellar2(sellar2_file, kind="CS")
disc_sellar_system = SellarSystem(sellar_system_file, kind="CS")

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
print(disc_sellar_1.jac)
print(disc_sellar_2.jac)
print(disc_sellar_system.jac)
