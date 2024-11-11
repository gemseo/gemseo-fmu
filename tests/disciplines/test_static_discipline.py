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
"""Tests for StaticFMUDiscipline."""

from __future__ import annotations

from inspect import getfullargspec

import pytest
from numpy import array

from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


@pytest.fixture(scope="module")
def add() -> StaticFMUDiscipline:
    """A static discipline based on 'add.fmu' model."""
    return StaticFMUDiscipline(get_fmu_file_path("add"))


def test_static_fmu_discipline_time():
    """Check that StaticFMUDiscipline is a BaseFMUDiscipline without time."""
    for arg in getfullargspec(StaticFMUDiscipline.__init__)[0]:
        assert "time" not in arg


def test_static_fmu_discipline_do_step():
    """Check that StaticFMUDiscipline is a BaseFMUDiscipline with do_step mode."""
    assert StaticFMUDiscipline(get_fmu_file_path("ramp"))._BaseFMUDiscipline__do_step


@pytest.mark.parametrize(
    ("input_data", "set_default_inputs", "result"),
    [
        ({}, False, 0),
        ({}, True, 1),
        (
            {
                "add.k1": array([1.0]),
                "u1": array([2.0]),
                "add.k2": array([3.0]),
                "u2": array([4.0]),
            },
            False,
            14,
        ),
        (
            {
                "add.k2": array([3.0]),
                "u2": array([4.0]),
            },
            True,
            13,
        ),
    ],
)
def test_execution_add(add, input_data, set_default_inputs, result):
    """Check the execution of the static discipline f(u) = k1*u1 + k2*u2."""
    if set_default_inputs:
        add.default_input_data.update({"add.k1": array([1.0]), "u1": array([1.0])})

    assert add.execute(input_data)["y"] == result
