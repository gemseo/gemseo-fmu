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
from numpy import searchsorted

from gemseo_fmu.utils.time_duration import TimeDuration

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from gemseo.typing import RealArray

    from gemseo_fmu.utils.time_duration import TimeDurationType


def plot_time_evolution(
    time: RealArray,
    data: Mapping[str, RealArray],
    abscissa_name: str = "",
    time_unit: TimeDuration.TimeUnit = TimeDuration.TimeUnit.SECONDS,
    time_window: int
    | tuple[int, int]
    | TimeDurationType
    | tuple[TimeDurationType, TimeDurationType] = 0,
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
    time_name = f"Time ({time_unit})"
    if not abscissa_name:
        abscissa_name = time_name

    if isinstance(time_window, int):
        time_window = (time_window, time.size)

    if isinstance(time_window, (float, str)):
        time_window = (
            searchsorted(time, TimeDuration(time_window).seconds) - 1,
            time.size,
        )

    if isinstance(time_window[0], (float, str)):
        time_window = (
            searchsorted(time, TimeDuration(time_window[0]).seconds) - 1,
            searchsorted(time, TimeDuration(time_window[1]).seconds),
        )

    dataset = Dataset()
    time_window = slice(*time_window)
    time_duration = TimeDuration(time[time_window, newaxis])
    dataset.add_variable(time_name, time_duration.to(time_unit))
    for name in set(data).union({abscissa_name}) - {time_name}:
        dataset.add_variable(name, data[name][time_window, newaxis])

    figure = Lines(dataset, list(data), abscissa_variable=abscissa_name)
    figure.execute(save=save, show=show, file_path=file_path)
    return figure
