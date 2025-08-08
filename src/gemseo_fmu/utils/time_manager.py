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
"""Time management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

LOGGER = logging.getLogger(__name__)


class TimeManager:
    """A time manager."""

    final: float
    """The final time."""

    step: float
    """The time step."""

    __current: float
    """The current time."""

    __initial: float
    """The initial time."""

    def __init__(self, initial: float, final: float, step: float) -> None:
        """
        Args:
            initial: The initial time.
            final: The final time.
            step: The time step.
        """  # noqa: D205, D212
        self.__current = self.__initial = initial
        self.final = final
        self.step = step

    @property
    def current(self) -> float:
        """The current time."""
        return self.__current

    @property
    def initial(self) -> float:
        """The initial time."""
        return self.__initial

    @property
    def remaining(self) -> float:
        """The remaining time."""
        return self.final - self.__current

    @property
    def is_initial(self) -> bool:
        """Whether the current time is the initial time."""
        return self.__current == self.__initial

    @property
    def is_final(self) -> bool:
        """Whether the current time is the final time."""
        return self.__current == self.final

    @property
    def is_constant(self) -> bool:
        """Whether the initial time is the final time."""
        return self.__initial == self.final

    def update_current_time(
        self, step: float = 0.0, return_time_manager: bool = True
    ) -> Self | tuple[float, float, float]:
        """Increment the current time by one time step and truncate at the final time.

        Args:
            step: The time step.
                If 0, use the time step passed at instantiation.
            return_time_manager: Whether to return the time evolution
                as a time manager.

        Returns:
            The current time before the update as initial time,
            the current time after the update as final time
            and the difference between the initial and final times as time step.
        """
        if not step:
            step = self.step

        if step > self.remaining:
            LOGGER.debug(
                "The time step is greater than the remaining time; "
                "use the remaining time instead."
            )
            step = self.remaining

        if step == 0:
            msg = (
                "The current time cannot be incremented "
                f"as it is the final time ({self.final})."
            )
            raise ValueError(msg)

        current_before_update = self.__current
        self.__current += step
        times = (current_before_update, self.__current, step)
        if return_time_manager:
            return self.__class__(*times)

        return times

    def reset(self) -> None:
        """Reset the time manager to initial time."""
        self.__current = self.__initial

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (
            self.current == other.current
            and self.initial == other.initial
            and self.step == other.step
            and self.final == other.final
        )
