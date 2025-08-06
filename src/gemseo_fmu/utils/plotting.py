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
"""Plotting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.datasets.dataset import Dataset
from gemseo.post.dataset.lines import Lines
from numpy import newaxis

from gemseo_fmu.utils.time_duration import TimeDuration

if TYPE_CHECKING:
    from collections.abc import Mapping
    from collections.abc import Sequence
    from pathlib import Path

    from gemseo.typing import RealArray


def plot_time_evolution(
    time: RealArray,
    data: Mapping[str, RealArray],
    abscissa_name: str = "",
    time_unit: TimeDuration.TimeUnit = TimeDuration.TimeUnit.SECONDS,
    time_window: int | Sequence[int] = 0,
    save: bool = True,
    show: bool = False,
    file_path: str | Path = "",
) -> Lines:
    """Plot the time evolution of variables.

    Args:
        time: The time steps.
        data: The values of the variables at time steps.
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
    time_name = f"Time ({time_unit})"
    if not abscissa_name:
        abscissa_name = time_name

    if isinstance(time_window, int):
        time_window = (time_window, time.size)

    dataset = Dataset()
    time_window = slice(*time_window)
    time_duration = TimeDuration(time[time_window, newaxis])
    dataset.add_variable(time_name, time_duration.to(time_unit))
    for name in set(data).union({abscissa_name}) - {time_name}:
        dataset.add_variable(name, data[name][time_window, newaxis])

    figure = Lines(dataset, list(data), abscissa_variable=abscissa_name)
    figure.execute(save=save, show=show, file_path=file_path)
    return figure
