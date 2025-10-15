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
"""Time duration."""

from __future__ import annotations

import delta

TimeDurationType = float | str


class TimeDuration:
    """A time duration.

    This time duration is instantiated
    either from a number expressed in seconds
    or a string of characters
    that is a `number[, , and ]unit` succession,
    e.g. `"2h 34m 1s"` or `"2 hours, 34 minutes and 1 second"`.
    The unit can be one of:

    - y, year, years,
    - m, month, months,
    - w, week, weeks,
    - d, day, days,
    - h, hour, hours,
    - min, minute, minutes,
    - s, second, seconds,
    - ms, millis, millisecond, milliseconds.

    The [value][gemseo_fmu.utils.time_duration.TimeDuration.value] attribute
    stores the numerical value of the time duration in seconds
    while a property whose name is a time unit, e.g. `years` or `minutes`,
    corresponds to the time duration expressed with this time unit.

    Lastly,
    [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration] objects can be compared,
    e.g. `assert TimeDuration("1 week") < TimeDuration("8 days")`.
    """

    class TimeUnit:
        """Time unit."""

        MICROSECONDS = "microseconds"
        MILLISECONDS = "milliseconds"
        SECONDS = "seconds"
        MINUTES = "minutes"
        HOURS = "hours"
        DAYS = "days"
        WEEKS = "weeks"
        MONTHS = "months"
        YEARS = "years"

    __value: float
    """The duration in seconds."""

    def __init__(self, duration: TimeDurationType) -> None:
        """
        Args:
            duration: The time duration.
        """  # noqa: D205, D212, D415
        self.value = duration

    @property
    def value(self) -> float:
        """The time duration in seconds."""
        return self.__value

    @value.setter
    def value(self, value: TimeDurationType) -> None:
        if isinstance(value, str):
            self.__value = delta.parse(value).total_seconds()
        else:
            self.__value = value

    def __eq__(self, other: TimeDuration) -> bool:
        return self.__value == other.value

    def __lt__(self, other: TimeDuration) -> bool:
        return self.__value < other.value

    def __le__(self, other: TimeDuration) -> bool:
        return self.__value <= other.value

    def __gt__(self, other: TimeDuration) -> bool:
        return self.__value > other.value

    def __ge__(self, other: TimeDuration) -> bool:
        return self.__value >= other.value

    @property
    def years(self) -> float:
        """The time duration in years."""
        return self.__value / 31557600

    @property
    def months(self) -> float:
        """The time duration in months."""
        return self.__value / 2629800

    @property
    def weeks(self) -> float:
        """The time duration in weeks."""
        return self.__value / 604800

    @property
    def days(self) -> float:
        """The time duration in days."""
        return self.__value / 86400

    @property
    def hours(self) -> float:
        """The time duration in hours."""
        return self.__value / 3600

    @property
    def minutes(self) -> float:
        """The time duration in minutes."""
        return self.__value / 60

    @property
    def seconds(self) -> float:
        """The time duration in seconds."""
        return self.__value

    @property
    def milliseconds(self) -> float:
        """The time duration in milliseconds."""
        return self.__value * 1000

    @property
    def microseconds(self) -> float:
        """The time duration in microseconds."""
        return self.__value * 1000000

    def to(self, time_unit: TimeUnit) -> float:
        """Return the time duration with a given time unit.

        Args:
            time_unit: The time unit.

        Returns:
            The time duration.
        """
        return getattr(self, time_unit)
