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

from collections.abc import Sequence
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

from gemseo.utils.pydantic_ndarray import NDArrayPydantic
from numpy import array
from pandas import read_csv
from pydantic.dataclasses import dataclass

from gemseo_fmu.utils.time_duration import TimeDuration
from gemseo_fmu.utils.time_duration import TimeDurationType

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

ObservableType = Sequence[float] | NDArrayPydantic[float]
"""The type for a sequence of observable values."""

TimeType = Sequence[TimeDurationType] | NDArrayPydantic
"""The type for a sequence of time values."""


@dataclass(frozen=True)
class TimeSeries:
    """The time series of an observable."""

    time: TimeType
    """The increasing values of the time.

    The components can be either numbers in seconds or strings of characters (see
    [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]).
    """

    observable: ObservableType
    """The values of the observable associated to the values of the time."""

    interpolate: bool = False
    """Whether to create a piecewise linear time function.

    Otherwise, create a piecewise constant time function.
    """

    tolerance: TimeDurationType = 0.0
    """The tolerance for the piecewise constant time function."""

    size: int = field(init=False)
    """The size of the time series."""

    compute: Callable[[float], float] = field(init=False)
    """The time function built from this time series."""

    def __post_init__(self) -> None:
        """
        Raises:
            ValueError: When the time and the observable have different lengths.
        """  # noqa: D205 D212 D415
        time_size = len(self.time)
        observable_size = len(self.observable)
        if time_size != observable_size:
            msg = (
                f"The lengths of fields 'time' ({time_size}) "
                f"and 'observable' ({observable_size}) do not match."
            )
            raise ValueError(msg)

        object.__setattr__(
            self,
            "compute",
            self.__piecewise_linear_function
            if self.interpolate
            else self.__piecewise_constant_function,
        )
        object.__setattr__(self, "size", time_size)
        object.__setattr__(self, "time", [TimeDuration(t).seconds for t in self.time])
        object.__setattr__(self, "tolerance", TimeDuration(self.tolerance).seconds)

    def __piecewise_constant_function(self, time: TimeDurationType) -> float:
        """The piecewise constant time function built from the time series.

        Args:
            time: The input value.

        Returns:
            The output value.
        """
        time = self.__check_time(time)
        for time_i, observable_i in zip(
            self.time[1:], self.observable[:-1], strict=False
        ):
            if time + self.tolerance < time_i:
                return observable_i

        return self.observable[-1]

    def __piecewise_linear_function(self, time: TimeDurationType) -> float:
        """The piecewise linear time function built from the time series.

        Args:
            time: The input value.

        Returns:
            The output value.
        """
        time = self.__check_time(time)
        for t_start, t_stop, o_start, o_stop in zip(
            self.time[:-1],
            self.time[1:],
            self.observable[:-1],
            self.observable[1:],
            strict=False,
        ):
            if time < t_stop:
                return o_start + (o_stop - o_start) / (t_stop - t_start) * (
                    time - t_start
                )

        return self.observable[-1]

    def __check_time(self, time: TimeDurationType) -> float:
        """Verify that a time is greater than the start time.

        Returns:
            The time as a float number.

        Raises:
            ValueError: When the input value is strictly lower than the initial time.
        """
        time = TimeDuration(time).seconds
        if time < self.time[0]:
            msg = f"The time series starts at {self.time[0]}; got {time}."
            raise ValueError(msg)

        return time

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return (array(self.time) == array(other.time)).all() and (
            array(self.observable) == array(other.observable)
        ).all()

    @classmethod
    def from_csv(
        cls,
        file_path: str | Path,
        tolerance: float = 0.0,
        header: int | Sequence[int] | Literal["infer"] | None = None,
        sep: str | None = ";",
        **kwargs: Any,
    ) -> TimeSeries:
        """Create a time series from a CSV file with two columns.

        Args:
            file_path: The CSV file path.
            tolerance: The tolerance for the piecewise constant time function.
            header: The ``header`` option of the ``pandas.read_csv`` function.
                By default, no header.
            sep: The ``sep`` option of the ``pandas.read_csv`` function.
            **kwargs: The options of the ``pandas.read_csv`` function.

        Returns:
            The time series.

        See Also:
            https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html.
        """
        data = read_csv(file_path, header=header, sep=sep, **kwargs).to_numpy()
        return cls(time=data[:, 0], observable=data[:, 1], tolerance=tolerance)
