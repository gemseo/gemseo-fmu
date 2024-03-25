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

from gemseo.datasets.dataset import Dataset
from gemseo.post.dataset.lines import Lines
from numpy import newaxis

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline
from gemseo_fmu.utils.time_duration import TimeDuration

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from gemseo.typing import NumberArray
    from gemseo.typing import RealArray


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

    TimeUnit = TimeDuration.TimeUnit

    @property
    def initial_values(self) -> dict[str, NumberArray]:
        """The initial input, output and time values."""
        return self._initial_values

    @property
    def time(self) -> RealArray | None:
        """The time steps of the last execution if any."""
        return self._time

    def plot(
        self,
        output_names: str | Iterable[str],
        abscissa_name: str = "",
        time_unit: TimeUnit = TimeUnit.SECONDS,
        time_window: int | tuple[int, int] = 0,
        save: bool = True,
        show: bool = False,
        file_path: str | Path = "",
    ) -> Lines:
        """Plot the time evolution of output variables.

        Args:
            output_names: The name(s) of the output variable(s).
            abscissa_name: The name of the variable to be plotted on the x-axis.
                If empty, use the time variable.
            time_unit: The unit to express the time.
            time_window: The time windows over which to draw the time evolution.
                Either the start time index (the end one will be the final time one)
                or both the start and end time indices.
            save: Whether to save the figure.
            show: Whether to show the figure.
            file_path: The path of the file to save the figure.
                The directory path and file format are deduced from it.
                If empty,
                save the file in the current directory,
                with the output name as file name and PNG format.

        Returns:
            The figure.
        """
        if isinstance(output_names, str):
            output_names = [output_names]

        time_name = f"Time ({time_unit})"
        if not abscissa_name:
            abscissa_name = time_name

        if isinstance(time_window, int):
            time_window = (time_window, self.time.size)

        dataset = Dataset()
        time_window = slice(*time_window)
        time_duration = TimeDuration(self.time[time_window, newaxis])
        dataset.add_variable(time_name, time_duration.to(time_unit))
        for name in set(output_names).union({abscissa_name}) - {time_name}:
            dataset.add_variable(name, self.local_data[name][time_window, newaxis])

        figure = Lines(dataset, output_names, abscissa_variable=abscissa_name)
        figure.execute(save=save, show=show, file_path=file_path)
        return figure
