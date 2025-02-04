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
    discipline.default_input_data["increment"] = 2.0
    discipline.execute()
    assert_almost_equal(discipline.time, array(time))
    assert_almost_equal(discipline.io.data["output"], array(output))
