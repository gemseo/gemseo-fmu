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
"""Tests for FMUDiscipline."""

from __future__ import annotations

import logging
import re
from typing import Any
from typing import NamedTuple
from unittest import mock
from unittest.mock import patch

import pytest
from fmpy.fmi2 import FMU2Slave
from fmpy.model_description import ModelDescription
from gemseo import from_pickle
from gemseo import to_pickle
from gemseo.utils.comparisons import compare_dict_of_arrays
from numpy import array
from numpy import ndarray
from numpy import ones
from numpy import zeros
from numpy.testing import assert_almost_equal
from numpy.testing import assert_equal

from gemseo_fmu.disciplines import base_fmu_discipline
from gemseo_fmu.disciplines import fmu_discipline
from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline
from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.disciplines.dynamic_fmu_discipline import DynamicFMUDiscipline
from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.problems.fmu_files import get_fmu_file_path
from gemseo_fmu.utils.time_series import TimeSeries

INPUT_NAME = "ramp.height"
OUTPUT_NAME = "out"
TIME = "time"

FMU_PATH = get_fmu_file_path("ramp")


@pytest.fixture(scope="module")
def ramp_discipline(module_tmp_wd) -> FMUDiscipline:
    """A ramp model y=f(x) with y=0 if x < 0, y=x if 0<=x<=1 and y=1 if > 1."""
    discipline = FMUDiscipline(FMU_PATH, [INPUT_NAME], [OUTPUT_NAME], final_time=1.0)
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    return discipline


@pytest.fixture
def ramp_discipline_wo_restart() -> FMUDiscipline:
    """A ramp model with custom time settings and without restart."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=0.0,
        final_time=0.6,
        time_step=0.2,
        restart=False,
    )
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    return discipline


@pytest.fixture(scope="module")
def ramp_discipline_w_restart(module_tmp_wd) -> FMUDiscipline:
    """A ramp discipline with custom time settings and with restart."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=0.0,
        final_time=0.6,
        time_step=0.2,
    )
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    return discipline


@pytest.fixture(scope="module")
def ramp_discipline_do_step(module_tmp_wd) -> FMUDiscipline:
    """A ramp discipline with custom time settings, without restart and with do_step."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=0.0,
        final_time=2.0,
        time_step=0.2,
        do_step=True,
        restart=False,
    )
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    return discipline


@pytest.fixture
def ramp_discipline_do_step_w_restart(tmp_wd) -> FMUDiscipline:
    """A FMU discipline with custom time settings, with restart and with do_step."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=0.0,
        final_time=2.0,
        time_step=0.2,
        do_step=True,
    )
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    return discipline


@pytest.fixture(scope="module")
def discipline() -> FMUDiscipline:
    """The MassSpringSystem discipline after execution."""
    discipline = FMUDiscipline(
        get_fmu_file_path("MassSpringSystem"), final_time=10, time_step=0.01
    )
    discipline.execute()
    return discipline


def test_do_step(ramp_discipline):
    """Check that the disciplines does not execute the FMU model step by step."""
    assert not ramp_discipline._BaseFMUDiscipline__do_step


def test_do_step_and_me(caplog):
    """Check that do_step cannot be used with ME models."""
    discipline = FMUDiscipline(
        FMU_PATH, [INPUT_NAME], [OUTPUT_NAME], do_step=True, use_co_simulation=False
    )
    assert discipline._BaseFMUDiscipline__model_type == "CoSimulation"
    assert (
        "gemseo_fmu.disciplines.base_fmu_discipline",
        logging.WARNING,
        "The FMUDiscipline 'ramp' requires a co-simulation model when do_step is True.",
    ) in caplog.record_tuples


def test_discipline_input_names(ramp_discipline):
    """Check the names of the discipline inputs."""
    assert set(ramp_discipline.io.input_grammar.names) == {INPUT_NAME}


def test_discipline_input_names_if_none(module_tmp_wd):
    """Check the names of the discipline inputs when input_names is None."""
    discipline = FMUDiscipline(FMU_PATH, None)
    assert not discipline.io.input_grammar.names


def test_discipline_input_names_if_empty(module_tmp_wd):
    """Check the names of the discipline inputs when input_names is empty."""
    discipline = FMUDiscipline(FMU_PATH, ())
    assert set(discipline.io.input_grammar.names) == {
        "ramp.duration",
        "ramp.height",
        "ramp.offset",
        "ramp.startTime",
    }


def test_discipline_output_names(ramp_discipline):
    """Check the names of the discipline outputs."""
    assert set(ramp_discipline.io.output_grammar.names) == {
        OUTPUT_NAME,
        "ramp_time",
    }


@pytest.mark.parametrize(
    ("use_input_namespace", "input_name"),
    [(False, INPUT_NAME), (True, f"ns:{INPUT_NAME}")],
)
@pytest.mark.parametrize(
    ("use_output_namespace", "output_name"),
    [(False, OUTPUT_NAME), (True, f"ns:{OUTPUT_NAME}")],
)
def test_namespace(
    ramp_discipline_do_step_w_restart,
    use_input_namespace,
    input_name,
    use_output_namespace,
    output_name,
):
    """Check that execution handles IO namespaces."""
    if use_input_namespace:
        ramp_discipline_do_step_w_restart.add_namespace_to_input(INPUT_NAME, "ns")
    if use_output_namespace:
        ramp_discipline_do_step_w_restart.add_namespace_to_output(OUTPUT_NAME, "ns")
    ramp_discipline_do_step_w_restart.execute({input_name: array([1.0])})
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[output_name], array([0.2])
    )


def test_str(ramp_discipline):
    """Check the string representation of a FMUDiscipline."""
    assert str(ramp_discipline) == "ramp"


def test_repr(ramp_discipline):
    """Check the string representation of a FMUDiscipline."""
    assert repr(ramp_discipline).startswith(
        "ramp\n   Inputs: ramp.height\n   Outputs: out, ramp_time\n\nModel Info"
    )


def test_default_inputs(ramp_discipline):
    """Check the default inputs of the discipline."""
    default_inputs = ramp_discipline.default_input_data
    assert set(default_inputs) == {INPUT_NAME}
    assert_equal(default_inputs[INPUT_NAME], array([2.0]))


def test_initial_values(ramp_discipline_wo_restart, ramp_discipline_do_step):
    """Check the initial values."""
    assert compare_dict_of_arrays(
        ramp_discipline_wo_restart.initial_values,
        {"out": array([None]), "ramp_time": array([0.0]), "ramp.height": array([1.0])},
    )
    assert compare_dict_of_arrays(
        ramp_discipline_do_step.initial_values,
        {"out": array([None]), "ramp_time": array([0.0]), "ramp.height": array([1.0])},
    )


def test_execute_without_do_step(ramp_discipline_wo_restart):
    """Check the execution from start to final time, w/o custom values and w/o restart.

    Here we consider a discipline not using restart by default.
    """
    ramp_discipline_wo_restart.execute()
    assert_almost_equal(ramp_discipline_wo_restart.time, array([0.0, 0.2, 0.4, 0.6]))
    assert_almost_equal(
        ramp_discipline_wo_restart.io.data[f"{ramp_discipline_wo_restart.name}_time"],
        array([0.0, 0.2, 0.4, 0.6]),
    )
    assert_almost_equal(
        ramp_discipline_wo_restart.io.data[OUTPUT_NAME],
        array([0.0, 0.4, 0.8, 1.2]),
    )
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The FMUDiscipline 'ramp' cannot be executed "
            "as its current time is its final time (0.6)."
        ),
    ):
        ramp_discipline_wo_restart.execute()


def test_execute_without_do_step_r(ramp_discipline_w_restart, caplog):
    """Check execution from initial to final times, w/o custom values and w/o restart.

    Here we consider a discipline using restart by default.
    """
    caplog.set_level(logging.DEBUG, "gemseo_fmu.utils.time_manager")
    time_data = array([0.0, 0.2, 0.4, 0.6])
    output_data = array([0.0, 0.4, 0.8, 1.2])
    ramp_discipline_w_restart.execute()
    assert_almost_equal(ramp_discipline_w_restart.time, time_data)
    assert_almost_equal(ramp_discipline_w_restart.io.data[OUTPUT_NAME], output_data)
    ramp_discipline_w_restart.execute()
    assert_almost_equal(ramp_discipline_w_restart.time, time_data)
    assert_almost_equal(ramp_discipline_w_restart.io.data[OUTPUT_NAME], output_data)
    ramp_discipline_w_restart.set_next_execution(simulation_time=0.8)
    ramp_discipline_w_restart.execute()
    assert_almost_equal(ramp_discipline_w_restart.time, time_data)
    assert_almost_equal(ramp_discipline_w_restart.io.data[OUTPUT_NAME], output_data)
    _, level, msg = caplog.record_tuples[0]
    assert level == logging.DEBUG
    assert msg == (
        "The time step is greater than the remaining time; "
        "use the remaining time instead."
    )


def test_execute_with_do_step(ramp_discipline_do_step):
    """Check the execution step by step, w/o custom values and w/o restart.

    Here we consider a discipline not using restart by default.
    """
    # One step forward with the standard ramp.
    ramp_discipline_do_step.execute()
    assert_almost_equal(ramp_discipline_do_step.time, array([0.2]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([0.4]))

    # One step forward with the standard ramp.
    ramp_discipline_do_step.execute()
    assert_almost_equal(ramp_discipline_do_step.time, array([0.4]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([0.8]))

    # One step forward with a custom ramp.
    ramp_discipline_do_step.execute({INPUT_NAME: array([1.0])})
    assert_almost_equal(ramp_discipline_do_step.time, array([0.6]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([0.6]))

    # One step forward with the standard ramp.
    ramp_discipline_do_step.execute()
    assert_almost_equal(ramp_discipline_do_step.time, array([0.8]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([1.6]))

    # One step forward with the standard ramp after restart.
    ramp_discipline_do_step.set_next_execution(restart=True)
    ramp_discipline_do_step.execute()
    assert_almost_equal(ramp_discipline_do_step.time, array([0.2]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([0.4]))

    # One step forward with a custom ramp.
    ramp_discipline_do_step.execute({INPUT_NAME: array([1.0])})
    assert_almost_equal(ramp_discipline_do_step.time, array([0.4]))
    assert_almost_equal(ramp_discipline_do_step.io.data[OUTPUT_NAME], array([0.4]))


def test_execute_with_do_step_r(ramp_discipline_do_step_w_restart):
    """Check the execution step by step, w/o custom values and w/o restart.

    Here we consider a discipline using restart by default.
    """
    # One step forward with the standard ramp.
    ramp_discipline_do_step_w_restart.execute()
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.2]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.4])
    )

    # One step forward with the standard ramp.
    ramp_discipline_do_step_w_restart.execute()
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.2]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.4])
    )

    # One step forward with a custom ramp.
    ramp_discipline_do_step_w_restart.execute({INPUT_NAME: array([1.0])})
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.2]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.2])
    )

    # One step forward with the standard ramp and a custom time step.
    ramp_discipline_do_step_w_restart.set_next_execution(time_step=0.1)
    ramp_discipline_do_step_w_restart.execute()
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.1]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.2])
    )

    # One step forward with the standard ramp without restart.
    ramp_discipline_do_step_w_restart.set_next_execution(restart=False)
    ramp_discipline_do_step_w_restart.execute()
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.3]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.6])
    )

    # One step forward with a custom ramp.
    ramp_discipline_do_step_w_restart.execute({INPUT_NAME: array([1.0])})
    assert_almost_equal(ramp_discipline_do_step_w_restart.time, array([0.2]))
    assert_almost_equal(
        ramp_discipline_do_step_w_restart.io.data[OUTPUT_NAME], array([0.2])
    )


@pytest.mark.parametrize("delete_model_instance_directory", [False, True])
def test_delete_fmu_instance_directory(delete_model_instance_directory, tmp_wd):
    """Check the argument delete_model_instance_directory."""
    model_instance_directory = tmp_wd / "foo"
    discipline = BaseFMUDiscipline(
        FMU_PATH,
        delete_model_instance_directory=delete_model_instance_directory,
        model_instance_directory=model_instance_directory,
    )
    with mock.patch.object(base_fmu_discipline, "rmtree") as mock_method:
        del discipline
        assert mock_method.called is delete_model_instance_directory
        if delete_model_instance_directory:
            mock_method.assert_called_with(model_instance_directory, ignore_errors=True)


def test_time_series():
    """Check the use of time series.

    Here is a test with the model y(t+1) = k1(t)u1(t) + k2(t)u2(t).

    t      k1(t)    u1(t)    k2(t)    u2(t)    y(t+1)
    0      1        1        1        0        1
    0.1    1        1        1        0        1
    0.2    1        1        1        0        1
    0.3    1        1        1        0        1
    0.4    1        1        1        0        1
    0.5    1        1        1        1        2
    0.6    1        1        1        1        2
    0.7    1        1        1        0        1
    0.8    1        1        1        0        1
    0.9    1        1        2        0        1
    1      1        1        2        0        1
    """
    discipline = FMUDiscipline(get_fmu_file_path("add"), final_time=1.0, time_step=0.1)
    discipline.execute()
    assert_almost_equal(discipline.io.data["y"], zeros([11]))
    discipline.execute({
        "u1": array([1.0]),
        "u2": TimeSeries([0.0, 0.5, 0.7], [0.0, 1.0, 0.0]),
        "add.k1": array([1.0]),
        "add.k2": TimeSeries([0.0, 0.9], [1.0, 2.0]),
    })
    assert_almost_equal(
        discipline.io.data[f"{discipline.name}_time"],
        array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    )
    assert_almost_equal(discipline.io.data["add.k1"], array([1.0]))
    assert_almost_equal(
        discipline.io.data["add.k2"],
        array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0]),
    )
    assert_almost_equal(discipline.io.data["u1"], array([1.0]))
    assert_almost_equal(
        discipline.io.data["u2"],
        array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]),
    )
    assert_almost_equal(
        discipline.io.data["y"],
        array([1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0]),
    )


def test_time_series_do_step():
    """Check the use of time series with do_step=True."""
    discipline = FMUDiscipline(
        get_fmu_file_path("add"),
        final_time=1.0,
        time_step=0.1,
        do_step=True,
        restart=False,
    )
    discipline.default_input_data.update({
        "u1": array([1.0]),
        "u2": TimeSeries([0.0, 0.5, 0.7], [0.0, 1.0, 0.0], tolerance=1e-3),
        "add.k1": array([1.0]),
        "add.k2": TimeSeries([0.0, 0.9], [1.0, 2.0], tolerance=1e-3),
    })
    time = []
    y = []
    u1 = []
    u2 = []
    k1 = []
    k2 = []
    for _ in range(10):
        result = discipline.execute()
        time.append(result[f"{discipline.name}_time"][0])
        y.append(result["y"][0])
        u1.append(result["u1"][0])
        u2.append(result["u2"][0])
        k1.append(result["add.k1"][0])
        k2.append(result["add.k2"][0])

    assert_almost_equal(
        time,
        array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]),
    )
    assert_almost_equal(k1, ones(10))
    assert_almost_equal(k2, array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0]))
    assert_almost_equal(u1, ones(10))
    assert_almost_equal(
        u2,
        array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]),
    )
    assert_almost_equal(
        y,
        array([1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0]),
    )


def test_fmu_model_description(ramp_discipline):
    """Check the property model_description."""
    assert isinstance(ramp_discipline.model_description, ModelDescription)


def test_fmu_model(ramp_discipline):
    """Check the property model."""
    assert isinstance(ramp_discipline.model, FMU2Slave)


def test_causalities_to_variable_names(ramp_discipline):
    """Check the property causalities_to_variable_names."""
    assert ramp_discipline.causalities_to_variable_names == {
        "output": ["out"],
        "parameter": ["ramp.duration", "ramp.height", "ramp.offset", "ramp.startTime"],
        "local": ["ramp.y"],
    }


@pytest.mark.parametrize("add_time_to_output_grammar", [False, True])
@pytest.mark.parametrize("do_step", [False, True])
def test_time_output_grammar(add_time_to_output_grammar, do_step):
    """Check the argument add_time_to_output_grammar."""
    discipline = FMUDiscipline(
        FMU_PATH,
        initial_time=0.0,
        time_step=0.2,
        final_time=1.0,
        add_time_to_output_grammar=add_time_to_output_grammar,
        do_step=do_step,
    )
    assert ("ramp_time" in discipline.output_grammar) == add_time_to_output_grammar
    assert "time" not in discipline.output_grammar
    data = discipline.execute()
    assert ("ramp_time" in data) is add_time_to_output_grammar


class DefaultExperiment(NamedTuple):
    startTime: float | None = None  # noqa: N815
    stopTime: float | None = None  # noqa: N815


@pytest.mark.parametrize(
    ("default_experiment", "expected_initial_time", "expected_final_time"),
    [
        (None, 1.5, 2.5),
        (DefaultExperiment(), 1.5, 2.5),
        (DefaultExperiment(startTime=1.0), 1.0, 2.5),
        (DefaultExperiment(stopTime=1.0), 1.5, 1.0),
        (DefaultExperiment(startTime=1.0, stopTime=1.0), 1.0, 1.0),
    ],
)
def test_get_default_time_value(
    default_experiment, expected_initial_time, expected_final_time
):
    """Check the private method __get_field_value."""
    get_default_time_value = FMUDiscipline._BaseFMUDiscipline__get_field_value
    assert (
        get_default_time_value(default_experiment, "startTime", 1.5)
        == expected_initial_time
    )
    assert (
        get_default_time_value(default_experiment, "stopTime", 2.5)
        == expected_final_time
    )


@pytest.mark.parametrize("as_default_input", [False, True])
@pytest.mark.parametrize(
    ("t0", "expected"), [(0, -4995.949237827578), (0.1, -4984.17842896)]
)
def test_time_series_default_inputs_or_input_data(as_default_input, t0, expected):
    """Test that FMUDiscipline can use TimeSeries in default_inputs and input_data."""
    discipline = FMUDiscipline(
        get_fmu_file_path("Mass_Damper"),
        ["mass.m", "spring.c"],
        ["y"],
        initial_time=0.0,
        final_time=1.0,
        time_step=0.0001,
    )
    custom_input_data = {"mass.m": TimeSeries(array([t0]), array([1.5]))}
    if as_default_input:
        discipline.default_input_data.update(custom_input_data)
        input_data = {}
    else:
        input_data = custom_input_data

    discipline.execute(input_data)
    assert discipline.io.data["y"].sum() == pytest.approx(expected)


@pytest.mark.parametrize("do_step", [False, True])
@pytest.mark.parametrize("restart", [False, True])
def test_serialize(tmp_wd, do_step, restart):
    """Verify the serialization of an FMUDiscipline."""
    file_path = "fmu_discipline.pkl"

    original_discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        time_step=0.2,
        final_time=1.0,
        do_step=do_step,
        restart=restart,
    )
    to_pickle(original_discipline, file_path)
    original_discipline.execute()

    discipline = from_pickle(file_path)
    discipline.execute()

    assert discipline._BaseFMUDiscipline__do_step == do_step
    assert discipline._BaseFMUDiscipline__default_simulation_settings.restart == restart
    assert_almost_equal(
        discipline.io.data[OUTPUT_NAME], original_discipline.io.data[OUTPUT_NAME]
    )


def test_initial_and_final_times_setter():
    """Check that FMUDiscipline.__set_final_time updates the default time settings.

    It is also a way to check that FMUDiscipline._pre_instantiate works correctly.
    """
    final_time = 3.0

    class NewFMUDiscipline(BaseFMUDiscipline):
        """A new FMU discipline."""

        def _pre_instantiate(self, **kwargs: Any) -> None:
            self._BaseFMUDiscipline__set_final_time(final_time)

    discipline = NewFMUDiscipline(FMU_PATH)
    settings = discipline._BaseFMUDiscipline__default_simulation_settings
    assert discipline._BaseFMUDiscipline__time_manager.final == final_time
    assert settings.simulation_time == final_time


@pytest.mark.parametrize(
    ("initial", "final", "step"), [(0.0, 1.0, 0.25), ("0s", "1s", "0.25s")]
)
def test_string_time(initial, final, step):
    """Verify that the times can be set from string values."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=initial,
        final_time=final,
        time_step=step,
    )
    discipline.execute()
    assert_equal(discipline.io.data[OUTPUT_NAME], array([0.0, 0.25, 0.5, 0.75, 1.0]))
    discipline.set_next_execution(simulation_time=final, time_step=step)
    discipline.execute()
    assert_equal(discipline.io.data[OUTPUT_NAME], array([0.0, 0.25, 0.5, 0.75, 1.0]))


def test_scalar_input_variables():
    """Check that an FMUDiscipline can use scalar input variables."""
    discipline = FMUDiscipline(
        FMU_PATH,
        [INPUT_NAME],
        [OUTPUT_NAME],
        initial_time=0.0,
        final_time=2.0,
        time_step=0.2,
    )
    discipline.default_input_data[INPUT_NAME] = array([2.0])
    discipline.execute()
    discipline.execute({INPUT_NAME: array([2.1])})
    output_data_with_array_input = discipline.io.data[OUTPUT_NAME]

    discipline.default_input_data[INPUT_NAME] = 2.0
    discipline.execute()
    discipline.execute({INPUT_NAME: 2.1})
    assert_equal(discipline.io.data[OUTPUT_NAME], output_data_with_array_input)


@pytest.mark.parametrize(
    ("cls", "warn"),
    [
        (FMUDiscipline, True),
        (DoStepFMUDiscipline, True),
        (DynamicFMUDiscipline, True),
        (StaticFMUDiscipline, False),
    ],
)
def test_zero_time_step_warning(caplog, cls, warn):
    """Check that a warning message is logged when the time step is zero."""
    discipline = cls(FMU_PATH)
    assert discipline._BaseFMUDiscipline__time_manager.step == 0.0
    assert (
        (
            "gemseo_fmu.disciplines.base_fmu_discipline",
            30,
            "The time step of the FMUDiscipline 'ramp' is equal to 0.",
        )
        in caplog.record_tuples
    ) is warn


def test_zero_time_step(caplog):
    """Check that no warning message is logged when the time step is not zero."""
    discipline = FMUDiscipline(FMU_PATH, time_step=0.2)
    assert discipline._BaseFMUDiscipline__time_manager.step == 0.2
    assert (
        "gemseo_fmu.disciplines.base_fmu_discipline",
        30,
        "The time step of the FMUDiscipline 'ramp' is equal to 0.",
    ) not in caplog.record_tuples


@pytest.mark.parametrize(
    (
        "do_step",
        "final_time",
        "restart",
        "time_step",
        "e_do_step",
        "e_final_time",
        "e_restart",
        "e_time_step",
    ),
    [
        (None, None, None, None, False, 1.0, True, 0.0),
        (True, 2.0, False, 0.2, True, 2.0, False, 0.2),
    ],
)
def test_set_default_execution(
    do_step,
    final_time,
    restart,
    time_step,
    e_do_step,
    e_final_time,
    e_restart,
    e_time_step,
):
    """Check the method set_default_execution."""
    d = FMUDiscipline(FMU_PATH)
    d.set_default_execution(
        do_step=do_step, final_time=final_time, restart=restart, time_step=time_step
    )
    default_simulation_settings = d._BaseFMUDiscipline__default_simulation_settings
    assert d._BaseFMUDiscipline__do_step is e_do_step
    assert default_simulation_settings.restart is e_restart
    assert d._BaseFMUDiscipline__time_manager.final == e_final_time
    assert default_simulation_settings.time_step == e_time_step


@pytest.mark.parametrize(
    ("variable_names", "offset_name", "output_name"),
    [
        ({}, "ramp.offset", "out"),
        ({"ramp.offset": "offset", "out": "output"}, "offset", "output"),
    ],
)
def test_variable_names(variable_names, offset_name, output_name):
    """Check the variable_names argument to rename the model variables."""
    discipline = FMUDiscipline(FMU_PATH, variable_names=variable_names)
    assert discipline.input_grammar.names == {
        "ramp.duration",
        "ramp.height",
        offset_name,
        "ramp.startTime",
    }
    assert discipline.output_grammar.names == {output_name, "ramp_time"}
    assert offset_name in discipline.default_input_data

    data = discipline.execute()
    assert_equal(data[offset_name], array([0.0]))
    assert_equal(data[output_name][0:3], array([0.0, 0.002, 0.004]))

    data = discipline.execute({offset_name: array([1.0])})
    assert_equal(data[offset_name], array([1.0]))
    assert_equal(data[output_name][0:3], array([1.0, 1.002, 1.004]))


def test_variable_names_exception():
    """Check that an exception is raised when variable_names used incorrect names."""
    with pytest.raises(
        ValueError, match=re.escape("{'a'} are not FMU variable names.")
    ):
        FMUDiscipline(FMU_PATH, variable_names={"a": "x"})


@pytest.mark.parametrize("is_default_value", [False, True])
def test_callable(is_default_value):
    """Check the use of a callable input."""
    fmu_discipline = FMUDiscipline(
        get_fmu_file_path("add"), time_step=1.0, final_time=3.0
    )
    input_data = {"u1": lambda time: time**2}
    if is_default_value:
        fmu_discipline.default_input_data.update(input_data)
        data = fmu_discipline.execute()
    else:
        data = fmu_discipline.execute(input_data)
    assert_equal(data["y"], array([0.0, 1.0, 4.0, 9.0]))


@pytest.mark.parametrize("validate", [None, True, False])
def test_fmu_validation_default(validate):
    """Check that the validate option is correctly passed."""
    with (
        patch(
            "gemseo_fmu.disciplines.base_fmu_discipline.instantiate_fmu"
        ) as mocked_instantiate_fmu,
        patch(
            "gemseo_fmu.disciplines.base_fmu_discipline.simulate_fmu"
        ) as mocked_simulate_fmu,
    ):
        fmu_file_path = get_fmu_file_path("add")
        if validate is None:
            discipline = FMUDiscipline(fmu_file_path)
            expected_validation_status = True
        else:
            discipline = FMUDiscipline(fmu_file_path, validate=validate)
            expected_validation_status = validate

        instantiate_kwargs = mocked_instantiate_fmu.call_args.kwargs
        assert instantiate_kwargs["require_functions"] is expected_validation_status

        discipline.execute()
        simulate_kwargs = mocked_simulate_fmu.call_args.kwargs
        assert simulate_kwargs["validate"] is expected_validation_status


def test_plot(discipline):
    """Check the function plot using mocks."""
    with mock.patch.object(
        fmu_discipline, "plot_time_evolution"
    ) as plot_time_evolution:
        discipline.plot(["x1"])

    plot_time_evolution.assert_called_once()
    assert isinstance(plot_time_evolution.call_args.args[0], ndarray)
    assert isinstance(plot_time_evolution.call_args.args[1]["x1"], ndarray)
    assert len(plot_time_evolution.call_args.args[1]) == 1
    assert plot_time_evolution.call_args.kwargs == {
        "abscissa_name": "",
        "file_path": "",
        "save": True,
        "show": False,
        "time_unit": "seconds",
        "time_window": 0,
    }


def test_plot_options(discipline):
    """Check the function plot using mocks and options."""
    with mock.patch.object(
        fmu_discipline, "plot_time_evolution"
    ) as plot_time_evolution:
        discipline.plot(
            ["x1"], "x2", time_unit=1, time_window=2, save=3, show=4, file_path=5
        )

    plot_time_evolution.assert_called_once()
    assert isinstance(plot_time_evolution.call_args.args[0], ndarray)
    assert isinstance(plot_time_evolution.call_args.args[1]["x1"], ndarray)
    assert len(plot_time_evolution.call_args.args[1]) == 2
    assert plot_time_evolution.call_args.kwargs == {
        "abscissa_name": "x2",
        "file_path": 5,
        "save": 3,
        "show": 4,
        "time_unit": 1,
        "time_window": 2,
    }


@pytest.mark.parametrize("add_time_to_output_grammar", [False, True])
def test_set_time_variable(add_time_to_output_grammar):
    """Check that the time variable is set correctly."""

    fmu_disc = FMUDiscipline(
        FMU_PATH, add_time_to_output_grammar=add_time_to_output_grammar
    )
    assert ("ramp_time" in fmu_disc._to_fmu_variables) is add_time_to_output_grammar
