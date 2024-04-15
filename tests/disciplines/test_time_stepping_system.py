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
"""Tests for TimeSteppingSystem."""

from __future__ import annotations

import pytest
from gemseo.disciplines.linear_combination import LinearCombination
from numpy.testing import assert_allclose

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


def test_standard_use():
    """Check that TimeSteppingSystem works correctly."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"), final_time=10, time_step=0.01
    )
    discipline.execute()
    x2_ref = discipline.local_data["x2"]

    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
            LinearCombination(["x2"], "x2_plus_one", offset=1),
        ),
        10,
        0.01,
    )
    system.execute()

    assert_allclose(system.local_data["x2"], x2_ref[1:])
    assert_allclose(
        system.local_data["x2_plus_one"][1:], system.local_data["x2"][:-1] + 1
    )


@pytest.mark.parametrize(
    ("kwargs", "n_calls"), [({}, 2), ({"restart": False}, 1), ({"restart": True}, 2)]
)
def test_restart(kwargs, n_calls):
    """Check the option restart."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        10,
        0.01,
        **kwargs,
    )
    system.execute()["x2"]
    assert system.execute()["x2"].size == 1000
    assert system.n_calls == n_calls


def test_do_step():
    """Check that TimeSteppingSystem works correctly in do_step mode."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"),
        final_time=10,
        time_step=0.01,
        do_step=True,
        restart=False,
    )
    discipline.execute()
    first_ref_x_2 = discipline.local_data["x2"]
    discipline.execute()
    second_ref_x_2 = discipline.local_data["x2"]
    assert first_ref_x_2 != second_ref_x_2

    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
            LinearCombination(["x2"], "x2_plus_one", offset=1),
        ),
        10,
        0.01,
        do_step=True,
        restart=False,
    )
    system.execute()
    first_system_x_2 = system.local_data["x2"]
    first_system_x_2_plus_one = system.local_data["x2_plus_one"]
    system.execute()
    second_system_x_2 = system.local_data["x2"]
    second_system_x_2_plus_one = system.local_data["x2_plus_one"]
    assert first_system_x_2 != second_system_x_2

    assert_allclose(first_system_x_2, first_ref_x_2)
    assert_allclose(first_system_x_2_plus_one, first_ref_x_2 + 1)
    assert_allclose(second_system_x_2, second_ref_x_2)
    assert_allclose(second_system_x_2_plus_one[1:], second_system_x_2[:-1] + 1)
