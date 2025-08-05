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
"""Tests for TimeSteppingSystem."""

from __future__ import annotations

import re

import pytest
from gemseo.disciplines.linear_combination import LinearCombination
from gemseo.mda.jacobi import MDAJacobi
from gemseo.mda.mda_chain import MDAChain
from numpy import array
from numpy.testing import assert_allclose
from numpy.testing import assert_equal

from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.time_stepping_system import TimeSteppingSystem
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from gemseo_fmu.utils.time_series import TimeSeries


@pytest.mark.parametrize("cls", [DoStepFMUDiscipline, FMUDiscipline])
def test_standard_use(cls):
    """Check that TimeSteppingSystem works correctly."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"), final_time=10, time_step=0.1
    )
    discipline.execute()
    x2_ref = discipline.io.data["x2"]

    # TimeSteppingSystem can use a mix of standard MDODisciplines,
    # BaseFMUDisciplines and FMU file paths.
    discipline = cls(get_fmu_file_path("MassSpringSubSystem1"))
    discipline.default_input_data["m1"] = discipline.default_input_data["m1"][0]
    system = TimeSteppingSystem(
        (
            discipline,
            get_fmu_file_path("MassSpringSubSystem2"),
            LinearCombination(["x2"], "x2_plus_one", offset=1),
        ),
        10,
        0.1,
    )
    system.execute()

    assert isinstance(system.mda, MDAChain)
    inner_mdas = system.mda.inner_mdas
    assert len(inner_mdas) == 1
    assert isinstance(inner_mdas[0], MDAJacobi)

    assert_allclose(system.io.data["x2"][:-1], x2_ref[1:])
    assert_allclose(system.io.data["x2_plus_one"], system.io.data["x2"] + 1)


@pytest.mark.parametrize(
    ("mda_max_iter_at_t0", "n_mda_exec", "n_disc_exec", "norm", "out1", "out2"),
    [(0, 1, 1, 1.0, 4.0, 5.0), (10, 2, 5, 0.527046, -5.0, -7.0)],
)
def test_mda_max_iter_at_t0(
    mda_max_iter_at_t0,
    n_mda_exec,
    n_disc_exec,
    norm,
    out1,
    out2,
    enable_discipline_statistics,
):
    """Check the use of an initial MDA to start from a multidisciplinary solution.

    We co-simulate two instances of FMU3Model:
    - the output of the first one is the input of the second one,
    - the input of the first one is the output of the second one,
    - the first one initializes its output to ``3 + input`` (increment = 1),
    - the second one initializes its output to ``3 + 2 * input`` (increment = 2).

    In the case mda_max_iter_at_t0=10,
    an MDA is performed at instantiation with a maximum of 10 iterations.
    The analytical solution is out1 =-6 and out2=-9.
    Then,
    after a time integration,
    these outputs are increased by 1 and 2 respectively.
    """
    discipline_1 = DoStepFMUDiscipline(
        get_fmu_file_path("FMU3Model"),
        variable_names={"input": "out2", "output": "out1", "increment": "inc1"},
    )
    discipline_2 = DoStepFMUDiscipline(
        get_fmu_file_path("FMU3Model"),
        variable_names={"input": "out1", "output": "out2", "increment": "inc2"},
    )
    discipline_2.default_input_data["inc2"] = 2.0
    tss = TimeSteppingSystem(
        (discipline_1, discipline_2),
        1,
        1,
        do_step=True,
        mda_max_iter_at_t0=mda_max_iter_at_t0,
    )
    tss.execute()
    assert tss._TimeSteppingSystem__mda.execution_statistics.n_executions == n_mda_exec
    assert discipline_1.execution_statistics.n_executions == n_disc_exec
    assert discipline_2.execution_statistics.n_executions == n_disc_exec
    data = tss.io.data
    assert_allclose(data["MDA residuals norm"], array([norm]), atol=1e-6)
    assert data["out1"] == array([out1])
    assert data["out2"] == array([out2])


@pytest.mark.parametrize(
    ("kwargs", "n_executions"),
    [({}, 2), ({"restart": False}, 1), ({"restart": True}, 2)],
)
@pytest.mark.parametrize("use_cache", [False, True])
def test_restart(kwargs, n_executions, use_cache, enable_discipline_statistics):
    """Check the option restart."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        5,
        1,
        **kwargs,
    )
    if system._TimeSteppingSystem__restart and not use_cache:
        system.set_cache(system.CacheType.NONE)

    system.execute()
    system.execute()
    assert_equal(
        system.io.data["MassSpringSubSystem1_time"], array([1.0, 2.0, 3.0, 4.0, 5.0])
    )
    assert system.io.data["x2"].size == 5
    assert system.execution_statistics.n_executions == n_executions


def test_do_step():
    """Check that TimeSteppingSystem works correctly in do_step mode."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"),
        final_time=10,
        time_step=0.01,
        do_step=True,
        restart=False,
    )
    discipline.execute()
    first_ref_x_2 = discipline.io.data["x2"]
    discipline.execute()
    second_ref_x_2 = discipline.io.data["x2"]
    assert first_ref_x_2 != second_ref_x_2

    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
            LinearCombination(["x2"], "x2_plus_one", offset=1),
        ),
        10,
        0.01,
        do_step=True,
        restart=False,
    )
    system.execute()
    first_system_x_2 = system.io.data["x2"]
    first_system_x_2_plus_one = system.io.data["x2_plus_one"]
    system.execute()
    second_system_x_2 = system.io.data["x2"]
    second_system_x_2_plus_one = system.io.data["x2_plus_one"]
    assert first_system_x_2 != second_system_x_2

    assert_allclose(first_system_x_2, first_ref_x_2)
    assert_allclose(first_system_x_2_plus_one, first_ref_x_2 + 1)
    assert_allclose(second_system_x_2, second_ref_x_2)
    assert_allclose(second_system_x_2_plus_one[1:], second_system_x_2[:-1] + 1)


def test_do_step_error():
    """Check that one cannot use do_step after final time."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        2,
        1,
        do_step=True,
        restart=False,
    )
    system.execute()
    system.execute()
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The current time cannot be incremented as it is the final time (2)."
        ),
    ):
        system.execute()


@pytest.mark.parametrize(
    ("apply", "step1", "step2"), [(True, 0.01, 0.01), (False, 0.004, 0.008)]
)
def test_apply_time_step_to_disciplines(apply, step1, step2):
    """Check the apply_time_step_to_disciplines argument."""
    s1 = DoStepFMUDiscipline(get_fmu_file_path("MassSpringSubSystem1"), time_step=0.004)
    s2 = DoStepFMUDiscipline(get_fmu_file_path("MassSpringSubSystem2"), time_step=0.008)
    system = TimeSteppingSystem(
        (s1, s2), 0.03, 0.01, apply_time_step_to_disciplines=apply
    )
    system.execute()
    assert s1._BaseFMUDiscipline__default_simulation_settings.time_step == step1
    assert s2._BaseFMUDiscipline__default_simulation_settings.time_step == step2
    expected_time = array([0.01, 0.02, 0.03])
    assert_equal(system.io.data["MassSpringSubSystem1_time"], expected_time)
    assert_equal(system.io.data["MassSpringSubSystem2_time"], expected_time)


def test_time_series():
    """Verify that TimeSteppingSystem can use TimeSeries input variables."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        0.3,
        0.1,
    )
    system.default_input_data.update({
        "m1": TimeSeries([0.0, 0.5, 0.8], [1.0, 1.5, 1.3])
    })
    system.execute()
    expected_time = array([0.1, 0.2, 0.3])
    assert_allclose(system.io.data["MassSpringSubSystem1_time"], expected_time)


def test_process_flow():
    """Check the process flow of the TimeSteppingSystem."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        0.3,
        0.1,
    )
    process_flow = system.get_process_flow()
    assert process_flow.get_disciplines_in_data_flow() == [system]

    mda_process_flow = system.mda.get_process_flow()
    assert process_flow.get_data_flow() == mda_process_flow.get_data_flow()

    execution_flow = process_flow.get_execution_flow()
    mda_execution_flow = mda_process_flow.get_execution_flow()
    assert execution_flow.disciplines == mda_execution_flow.disciplines
    assert len(execution_flow.sequences) == len(mda_execution_flow.sequences) == 1
    assert type(execution_flow.sequences[0]) is type(mda_execution_flow.sequences[0])


@pytest.mark.parametrize(
    ("mda_name", "expected"),
    [
        ("MDAJacobi", array([1.0, 0.98, 0.941])),
        ("MDAGaussSeidel", array([1.0, 0.981, 0.9441])),
    ],
)
def test_mda_name(mda_name, expected):
    """Check a custom MDA."""
    system = TimeSteppingSystem(
        (
            get_fmu_file_path("MassSpringSubSystem1"),
            get_fmu_file_path("MassSpringSubSystem2"),
        ),
        0.3,
        0.1,
        mda_name=mda_name,
    )
    system.execute()
    assert_allclose(system.io.data["x2"], expected, atol=1e-5)
