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
from __future__ import annotations

from pathlib import Path
from unittest import mock

import gemseo_fmu.problems.fmu_files as fmus
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


@mock.patch("gemseo_fmu.problems.fmu_files.PLATFORM_IS_WINDOWS", False)
def test_get_fmu_file_path_without_windows():
    """Check get_fmu_file_path() with another OS than Windows (assumed to be linux)."""
    assert get_fmu_file_path("foo") == Path(fmus.__file__).parent / "linux" / "foo.fmu"
    assert (
        get_fmu_file_path("foo", "bar")
        == Path(fmus.__file__).parent / "linux" / "bar" / "foo.fmu"
    )


@mock.patch("gemseo_fmu.problems.fmu_files.PLATFORM_IS_WINDOWS", True)
def test_get_fmu_file_path_with_windows():
    """Check get_fmu_file_path() under Windows."""
    assert get_fmu_file_path("foo") == Path(fmus.__file__).parent / "win32" / "foo.fmu"
    assert (
        get_fmu_file_path("foo", "bar")
        == Path(fmus.__file__).parent / "win32" / "bar" / "foo.fmu"
    )
