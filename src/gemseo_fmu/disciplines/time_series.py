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
"""Time series."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class TimeSeries:
    """The time series of an observable."""

    time: Sequence[float]
    """The increasing values of the time."""

    observable: Sequence[float]
    """The values of the observable associated to the values of the time."""

    size: int = field(init=False)
    """The size of the time series."""

    def __post_init__(self) -> None:
        """
        Raises:
            ValueError: When the time and the observable have different lengths.
        """  # noqa: D205 D212 D415
        time_size = len(self.time)
        observable_size = len(self.observable)
        if time_size != observable_size:
            raise ValueError(
                f"The lengths of fields 'time' ({time_size}) "
                f"and 'observable' ({observable_size}) do not match."
            )
        object.__setattr__(self, "size", time_size)
