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
from pathlib import Path

import pytest
from gemseo.api import create_design_space
from gemseo.api import create_scenario
from numpy import array
from numpy import ones

from problems.sellar import Sellar1, Sellar2, SellarSystem

FMU_DIRECTORY_PATH = Path(__file__).parent.parent / "fmu_files"


@pytest.fixture()
def fmu_disciplines():
    """Build all fmu discipline for Sellar problem."""
    sellar1 = Sellar1(FMU_DIRECTORY_PATH / "SellarDis1.fmu", kind="CS")
    sellar2 = Sellar2(FMU_DIRECTORY_PATH / "SellarDis2.fmu", kind="CS")
    sellar_system = SellarSystem(FMU_DIRECTORY_PATH / "SellarSystem.fmu", kind="CS")
    return [sellar1, sellar2, sellar_system]


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


def test_fmu_jacobians_sellar1(fmu_disciplines):
    """Check that jacobian matrices returned by fmu functions are correct with respect
    to finite difference computation for Sellar1."""
    sellar1, sellar2, sellar_system = fmu_disciplines

    threshold = 1
    step = 1e-7

    assert sellar1.check_jacobian(step=step, threshold=threshold)
    assert sellar2.check_jacobian(step=step, threshold=threshold)
    assert sellar_system.check_jacobian(step=step, threshold=threshold)


def test_fmu_optim_results(fmu_scenario):
    """Test obtained optimal values when solving sellar problem with fmu discipline.

    Jacobians are computed.
    """
    fmu_scenario.execute(input_data={"max_iter": 20, "algo": "SLSQP"})

    optim_res = fmu_scenario.get_optimum()
    x_opt = fmu_scenario.design_space.get_current_x_dict()

    assert pytest.approx(optim_res.f_opt) == 3.188547
    assert pytest.approx(x_opt["x_local"]) == 0.0
    assert pytest.approx(x_opt["x_shared_1"]) == 1.77855793
    assert pytest.approx(x_opt["x_shared_2"]) == 0.0
    assert pytest.approx(x_opt["y_1"]) == 1.77763888
    assert pytest.approx(x_opt["y_2"]) == 3.55619681
