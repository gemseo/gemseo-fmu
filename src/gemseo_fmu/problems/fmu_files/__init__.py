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
"""A set of platform-dependent FMU files."""

from __future__ import annotations

from pathlib import Path

from gemseo.utils.portable_path import PLATFORM_IS_WINDOWS


def get_fmu_file_path(model_name: str, directory_name: str = ".") -> Path:
    """Return the file path of an FMU model depending on the platform.

    Args:
        model_name: The name of the FMU model;
            the corresponding file name is ``f"{model_name}.fmu"``.
        directory_name: The name of the directory containing the file.

    Returns:
        The file path of the FMU model.
    """
    os_dir = "win32" if PLATFORM_IS_WINDOWS else "linux"
    return Path(__file__).parent / os_dir / directory_name / f"{model_name}.fmu"
