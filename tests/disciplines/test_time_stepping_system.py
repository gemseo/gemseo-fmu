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
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from numpy.testing import assert_allclose


def test_standard_use():
    """Check that TimeSteppingSystem works correctly."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"), final_time=10, time_step=0.01
    )
    discipline.execute()
    x2_ref = discipline.local_data["x2"]

    discipline = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
            LinearCombination(["x2"], "x2_plus_one", offset=1),
        ),
        10,
        0.01,
    )
    discipline.execute()

    assert_allclose(discipline.local_data["x2"], x2_ref[1:])
    assert_allclose(discipline.local_data["x2_plus_one"], x2_ref[1:] + 1, rtol=1e-1)


@pytest.mark.parametrize(
    ("kwargs", "n_calls"), [({}, 2), ({"restart": False}, 1), ({"restart": True}, 2)]
)
def test_restart(kwargs, n_calls):
    """Check the option restart."""
    discipline = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        10,
        0.01,
        **kwargs,
    )
    discipline.execute()["x2"]
    assert discipline.execute()["x2"].size == 1000
    assert discipline.n_calls == n_calls


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
    first_x_2_ref = discipline.local_data["x2"]
    discipline.execute()
    second_x_2_ref = discipline.local_data["x2"]
    assert first_x_2_ref != second_x_2_ref

    discipline = TimeSteppingSystem(
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
    discipline.execute()
    first_x_2_system = discipline.local_data["x2"]
    first_x_2_system_plus_one = discipline.local_data["x2_plus_one"]
    discipline.execute()
    second_x_2_system = discipline.local_data["x2"]
    second_x_2_system_plus_one = discipline.local_data["x2_plus_one"]
    assert first_x_2_system != second_x_2_system

    assert_allclose(first_x_2_system, first_x_2_ref)
    assert_allclose(first_x_2_system_plus_one, first_x_2_ref + 1)
    assert_allclose(second_x_2_system, second_x_2_ref)
    assert_allclose(second_x_2_system_plus_one, second_x_2_ref + 1, rtol=1e-1)
