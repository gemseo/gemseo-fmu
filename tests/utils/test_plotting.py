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

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import mock

import pytest
from gemseo.utils.testing.helpers import image_comparison

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from gemseo_fmu.utils.plotting import Lines
from gemseo_fmu.utils.plotting import plot_time_evolution
from gemseo_fmu.utils.time_duration import TimeDuration

if TYPE_CHECKING:
    from gemseo.typing import RealArray


@pytest.fixture(scope="module")
def discipline() -> FMUDiscipline:
    """The MassSpringSystem discipline after execution."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"), final_time=10, time_step=0.01
    )
    discipline.execute()
    return discipline


@pytest.fixture(scope="module")
def time(discipline) -> RealArray:
    """The time steps."""
    return discipline.time


@pytest.fixture(scope="module")
def data(discipline) -> RealArray:
    """The time evolution of the variables of interest."""
    return discipline.io.data


@pytest.mark.parametrize(
    ("baseline_images", "output_names"),
    [(["one_output"], "x1"), (["two_outputs"], ["x1", "x2"])],
)
@image_comparison(None)
def test_plot(time, data, baseline_images, output_names):
    """Verify that the discipline can plot the last execution."""
    plot_time_evolution(
        time, {k: v for k, v in data.items() if k in output_names}, save=False
    )


@image_comparison(["time_unit"])
def test_plot_time_unit(time, data):
    """Verify that the discipline can plot the last execution with a given time unit."""
    plot_time_evolution(
        time, {"x1": data["x1"]}, save=False, time_unit=TimeDuration.TimeUnit.MINUTES
    )


@image_comparison(["abscissa_name"])
def test_plot_abscissa_name(time, data):
    """Verify that the discipline can plot the last execution wrt a variable."""
    plot_time_evolution(
        time, {"x1": data["x1"], "x2": data["x2"]}, save=False, abscissa_name="x2"
    )


@image_comparison(["time_window_as_integer"])
def test_plot_time_window_as_integer(time, data):
    """Verify that the discipline can plot the last execution from a time index."""
    plot_time_evolution(time, {"x1": data["x1"]}, save=False, time_window=500)


@image_comparison(["time_window_as_integer_tuple"])
def test_plot_time_window_as_integer_tuple(time, data):
    """Verify that the discipline can plot the last execution from time indices."""
    plot_time_evolution(time, {"x1": data["x1"]}, save=False, time_window=(500, 700))


@pytest.mark.parametrize("time_window", [3.0, "3 seconds"])
@image_comparison(["time_window_as_float"])
def test_plot_time_window_as_float(time, data, time_window):
    """Verify that the discipline can plot the last execution from a time value."""
    plot_time_evolution(time, {"x1": data["x1"]}, save=False, time_window=time_window)


@pytest.mark.parametrize("time_window", [(3.0, 7.0), ("3 seconds", "7 seconds")])
@image_comparison(["time_window_as_float_tuple"])
def test_plot_time_window_as_float_tuple(time, data, time_window):
    """Verify that the discipline can plot the last execution from time values."""
    plot_time_evolution(time, {"x1": data["x1"]}, save=False, time_window=time_window)


def test_plot_options(time, data):
    """Verify that FMUDiscipline.plot correctly uses save, show and file_path."""
    with mock.patch.object(Lines, "execute") as execute:
        figure = plot_time_evolution(
            time, {"x1": data["x1"]}, show=True, file_path="foo.png"
        )

    assert isinstance(figure, Lines)
    assert execute.call_args.kwargs == {
        "save": True,
        "show": True,
        "file_path": "foo.png",
    }
