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
"""Tests for the Sellar problem based on FMU models."""
from __future__ import annotations

import numpy as np
import pytest
from gemseo import create_design_space
from gemseo import create_scenario
from gemseo_fmu.problems.disciplines.sellar.sellar_1 import FMUSellar1
from gemseo_fmu.problems.disciplines.sellar.sellar_2 import FMUSellar2
from gemseo_fmu.problems.disciplines.sellar.sellar_system import FMUSellarSystem
from numpy import array
from numpy import ones
from numpy import zeros


def get_xzy():
    """Generate initial solution."""
    x_local = array([0.0])
    x_shared = array([1.0, 0.0])
    y_1 = zeros(1)
    y_2 = zeros(1)
    return x_local, x_shared, y_1, y_2


@pytest.fixture()
def fmu_disciplines():
    """Build all FMU disciplines for Sellar problem."""
    return [FMUSellar1(), FMUSellar2(), FMUSellarSystem()]


@pytest.fixture()
def fmu_scenario(fmu_disciplines):
    """Build the Sellar scenario for fmu tests."""
    design_space = create_design_space()
    design_space.add_variable("x_local", 1, l_b=0.0, u_b=10.0, value=ones(1))
    design_space.add_variable("x_shared_1", 1, l_b=-10, u_b=10.0, value=array([4.0]))
    design_space.add_variable("x_shared_2", 1, l_b=0.0, u_b=10.0, value=array([3.0]))
    design_space.add_variable("y_1", 1, l_b=-100.0, u_b=100.0, value=ones(1))
    design_space.add_variable("y_2", 1, l_b=-100.0, u_b=100.0, value=ones(1))

    scenario = create_scenario(
        fmu_disciplines,
        formulation="IDF",
        objective_name="obj",
        design_space=design_space,
    )

    scenario.add_constraint("c_1", "ineq")
    scenario.add_constraint("c_2", "ineq")

    return scenario


def test_fmu_sellar_jacobians_check(fmu_disciplines):
    """Check that the Jacobian matrices returned by fmu functions are correct."""
    sellar1, sellar2, sellar_system = fmu_disciplines

    threshold = 1
    step = 1e-7

    for discipline in [sellar1, sellar2, sellar_system]:
        discipline.set_cache_policy("SimpleCache")
        assert discipline.check_jacobian(step=step, threshold=threshold)


def test_fmu_sellar_computations(fmu_disciplines):
    """Check that the computed values returned by fmu functions are correct."""
    sellar1, sellar2, sellar_system = fmu_disciplines
    x_local, x_shared, y_1, y_2 = get_xzy()

    assert sellar1.compute_y_1(x_local, x_shared, y_2) == (1 + 0j)
    assert sellar2.compute_y_2(x_shared, y_1) == 1.0
    assert sellar2.compute_y_2(array([-1.0, 0.0]), array([1.0])) == 0.0
    assert sellar2.compute_y_2(array([-1.0, 0.0]), array([-1.0])) == 0.0
    assert sellar_system.compute_c_1(y_1) == 3.16
    assert sellar_system.compute_c_2(y_2) == -24.0
    assert np.allclose(
        sellar_system.compute_obj(x_local, x_shared, y_1, y_2), array([1.0 + 0.0j])
    )


def test_fmu_optim_results(fmu_scenario):
    """Test obtained optimal values when solving sellar problem with fmu discipline."""
    fmu_scenario.execute(input_data={"max_iter": 20, "algo": "SLSQP"})
    assert pytest.approx(fmu_scenario.optimization_result.f_opt) == 3.1700465222385836
