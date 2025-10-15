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
from gemseo_fmu.utils.plotting import plot_time_evolution
from gemseo_fmu.utils.time_duration import TimeDuration

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from gemseo.post.dataset.lines import Lines
    from gemseo.typing import NumberArray
    from gemseo.typing import RealArray

    from gemseo_fmu.utils.time_duration import TimeDurationType


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
        return {
            name: variable.initial for name, variable in self._to_fmu_variables.items()
        }

    @property
    def time(self) -> RealArray | None:
        """The time steps of the last execution if any."""
        return self._time

    def plot(
        self,
        output_names: str | Iterable[str],
        abscissa_name: str = "",
        time_unit: TimeUnit = TimeUnit.SECONDS,
        time_window: int
        | tuple[int, int]
        | TimeDurationType
        | tuple[TimeDurationType, TimeDurationType] = 0,
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
            time_window: The time window over which to draw the time evolution.
                Either the index of the initial time,
                the indices of the initial and final times,
                the initial time,
                or the initial and final times.
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
        return plot_time_evolution(
            self._time,
            {
                k: v
                for k, v in self.io.data.items()
                if k in output_names or k == abscissa_name
            },
            abscissa_name=abscissa_name,
            time_unit=time_unit,
            time_window=time_window,
            save=save,
            show=show,
            file_path=file_path,
        )
