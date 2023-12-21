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
"""A dynamic discipline wrapping a Functional Mockup Unit (FMU) model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline

if TYPE_CHECKING:
    from numpy.typing import NDArray


class FMUDiscipline(BaseFMUDiscipline):
    """A dynamic discipline wrapping a Functional Mockup Unit (FMU) model.

    This discipline relies on [FMPy](https://github.com/CATIA-Systems/FMPy).

    Notes:
        The time series are interpolated at the time steps
        resulting from the union of their respective time steps.
        Then,
        between two time steps,
        the time series for the variables of causality "input" are linearly interpolated
        at the *integration* time steps
        while for the variables of causality "parameter",
        the time series are considered as constant.
    """

    @property
    def initial_values(self) -> dict[str, NDArray[float]]:
        """The initial input, output and time values."""
        return self._initial_values

    @property
    def time(self) -> NDArray[float] | None:
        """The time steps of the last execution if any."""
        return self._time
