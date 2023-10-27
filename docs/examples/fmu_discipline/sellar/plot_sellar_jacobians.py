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
"""# Create a discipline for the Sellar problem from an FMU file and compute its
Jacobians"""
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
