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
"""Tests for DoStepFMUDiscipline."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def fmu_file_path() -> Path:
    """The file path to the ramp FMU model."""
    return get_fmu_file_path("ramp")


@pytest.fixture(scope="module")
def discipline(fmu_file_path) -> DoStepFMUDiscipline:
    """A DoStepFMUDiscipline based on the ramp FMU model."""
    return DoStepFMUDiscipline(fmu_file_path)


def test_do_step(discipline, fmu_file_path):
    """Check that a DoStepFMUDiscipline is an FMUDiscipline with do_step=True."""
    assert discipline._BaseFMUDiscipline__do_step is True


def test_do_step_cannot_be_set(discipline, fmu_file_path):
    """Check that setting do_step raises a ValueError only if False."""
    DoStepFMUDiscipline(fmu_file_path, do_step=True)
    assert discipline._BaseFMUDiscipline__do_step is True

    with pytest.raises(
        ValueError, match=re.escape("DoStepFMUDiscipline has no do_step parameter.")
    ):
        DoStepFMUDiscipline(fmu_file_path, do_step=False)


def test_co_simulation(discipline):
    """Check that a DoStepFMUDiscipline is an FMUDiscipline with CS type."""
    assert discipline._BaseFMUDiscipline__model_type == "CoSimulation"


def test_restart(discipline):
    """Check that the default value of restart is False."""
    assert not discipline._BaseFMUDiscipline__default_simulation_settings.restart
