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
"""Tests for gemseo_fmu."""
from __future__ import annotations

from gemseo_fmu import FMUDiscipline
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline as OriginalFMUDiscipline


def test_fmu_discipline():
    """Check that FMUDiscipline can be imported from gemseo_fmu."""
    assert FMUDiscipline == OriginalFMUDiscipline
