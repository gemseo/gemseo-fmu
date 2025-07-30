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

import pytest
from numpy import array
from numpy.testing import assert_almost_equal
from numpy.testing import assert_equal

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


@pytest.mark.parametrize(
    ("do_step", "time", "output"),
    [
        (False, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], [3.0, 5.0, 7.0, 9.0, 11.0, 13.0]),
        (True, [0.2], [5.0]),
    ],
)
def test_fmu3(do_step, time, output):
    """Check that gemseo-fmu can handle FMU3 models."""
    discipline = FMUDiscipline(
        get_fmu_file_path("FMU3Model"), final_time=1.0, time_step=0.2, do_step=do_step
    )
    discipline.io.input_grammar.defaults["increment"] = 2.0
    discipline.execute()
    assert_almost_equal(discipline.time, array(time))
    assert_almost_equal(discipline.io.data["output"], array(output))


def test_data_types():
    """Check that gemseo-fmu can handle FMU3 with different kinds of data."""
    discipline = FMUDiscipline(
        get_fmu_file_path("FMU3Model"), final_time=1.0, time_step=0.2
    )
    defaults = discipline.io.input_grammar.defaults
    assert_equal(defaults["int32"], array([6]))
    assert_equal(defaults["int64"], array([7]))
    assert_equal(defaults["float64"], array([7.23]))
    assert_equal(defaults["boolean"], array([True]))
    assert_equal(defaults["string"], array(["foo"]))
    assert_equal(defaults["enumeration"], array([1]))
    discipline.execute({
        "int32": 11,
        "int64": 12,
        "float64": 13.14,
        "boolean": False,
        "string": "bar",
        "enumeration": 3,
    })
    model = discipline._BaseFMUDiscipline__model
    to_fmu_variables = discipline._to_fmu_variables
    assert model.getInt32([to_fmu_variables["int32"].reference]) == [11]
    assert model.getInt64([to_fmu_variables["int64"].reference]) == [12]
    assert model.getFloat64([to_fmu_variables["float64"].reference]) == [13.14]
    assert model.getBoolean([to_fmu_variables["boolean"].reference]) == [False]
    assert model.getString([to_fmu_variables["string"].reference]) == ["bar"]
    assert model.getInt64([to_fmu_variables["enumeration"].reference]) == [3]


@pytest.mark.parametrize(
    ("do_step", "output_vector"),
    [
        (
            False,
            array([
                [0.0, 1.0, 2.0, 3.0, 4.0],
                [4.0, 0.0, 1.0, 2.0, 3.0],
                [3.0, 4.0, 0.0, 1.0, 2.0],
                [2.0, 3.0, 4.0, 0.0, 1.0],
                [1.0, 2.0, 3.0, 4.0, 0.0],
                [0.0, 1.0, 2.0, 3.0, 4.0],
            ]),
        ),
        (True, array([4.0, 0.0, 1.0, 2.0, 3.0])),
    ],
)
def test_array(do_step, output_vector):
    """Checks that gemseo-fmu can handle array outputs (FMU3 models)."""
    discipline = FMUDiscipline(
        get_fmu_file_path("FMU3Model"), final_time=1.0, time_step=0.2, do_step=do_step
    )
    discipline.execute()
    assert_equal(discipline.io.data["vector"], output_vector)
