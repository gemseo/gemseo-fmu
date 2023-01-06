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
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or initial documentation
#        :author: Jorge CAMACHO CASERO
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""Tests for FMUDiscipline."""
import re
import sys
from pathlib import Path
from typing import Any

import pytest
from gemseo_fmu.fmu_discipline import FMUDiscipline
from numpy import array
from numpy import sin
from pyfmi.fmi import FMUException

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform


def _discipline(file_name: str = "Mass_Damper.fmu", **kwargs: Any) -> FMUDiscipline:
    return FMUDiscipline(FMU_DIR_PATH / file_name, kind="CS", **kwargs)


discipline = pytest.fixture(_discipline)


def _discipline_history(
    file_name: str = "Mass_Damper.fmu", **kwargs: Any
) -> FMUDiscipline:
    return FMUDiscipline(
        FMU_DIR_PATH / file_name, kind="CS", history_outputs=["y"], **kwargs
    )


discipline_history = pytest.fixture(_discipline_history)


def _discipline_with_inputs(
    file_name: str = "Mass_Damper.fmu", **kwargs: Any
) -> FMUDiscipline:
    disc = FMUDiscipline(
        FMU_DIR_PATH / file_name,
        kind="CS",
        simulate_options={"input": ("f", sin), "start_time": 0, "final_time": 1},
        **kwargs,
    )
    return disc


discipline_with_inputs = pytest.fixture(_discipline_with_inputs)


def test_fmu_kind(discipline):
    """Tests if the model is either of type Model Exchange or Co-Simulation."""
    assert discipline._kind in ("ME", "CS")


def test_inputs_names_from_fmu(discipline):
    """Test input variables read from fmu file.

    GEMSEO input grammar is defined from FMU model causalities 0 and 2 (i.e. the FMU
    parameters and FMU input variables)
    """
    assert discipline.get_input_data_names() == [
        "f",
        "damper.d",
        "damper.s_nominal",
        "fixed.s0",
        "mass.L",
        "mass.m",
        "spring.c",
        "spring.s_rel0",
    ]


def test_outputs_names_from_fmu(discipline):
    """Test output variables read from fmu file; GEMSEO output grammar is defined from
    FMU model causalities 1 (i.e. the FMU output variables)"""
    assert discipline.get_output_data_names() == ["y"]


def test_raises_fmu_file_not_provided():
    """Test that a fmu file is provided to the discipline."""
    msg = "__init__() missing 1 required positional argument: 'fmu_file_path'"
    with pytest.raises(TypeError, match=re.escape(msg)):
        FMUDiscipline()


def test_raises_fmu_file_not_available():
    """Test if the fmu file exists in the specified directory."""
    msg = "Could not locate the FMU in the specified directory."
    with pytest.raises(FMUException, match=msg):
        FMUDiscipline("missing_file.fmu")


def test_simulation_options():
    """Test if the simulation options provided by the user are PyFMI options."""
    options = {
        "start_time": 0.0,
        "final_time": 1.0,
        "algorithm": "FMICSAlg",
        "pyfmi_options": {
            "ncp": 510,
            "initialize": True,
            "not_a_simulation_option": None,
        },
    }
    msg = (
        "Some simulation options are no PyFMI simulation option. "
        "See simulation_options()."
    )

    with pytest.raises(ValueError, match=msg):
        _discipline(simulate_options=options)


def test_history(discipline_history):
    """Test that the discipline history is correctly created for the selected
    variables."""
    discipline_history.execute()
    assert (
        discipline_history.local_data["y" + "_history"]
        == discipline_history.simulation_results["y"]
    ).all()


def test_available_simulate_options(discipline_with_inputs):
    """Test that the available options returned the right values."""
    simulate_options = {
        "filter": None,
        "initialize": True,
        "ncp": 500,
        "result_file_name": "",
        "result_handler": None,
        "result_handling": "binary",
        "result_store_variable_description": True,
        "return_result": True,
        "silent_mode": False,
        "stop_time_defined": False,
        "time_limit": None,
        "write_scaled_result": False,
    }
    assert discipline_with_inputs.simulation_options == simulate_options


def test_model_simulation_results(discipline_with_inputs):
    """Test that the simulation results returned are right."""
    assert (
        discipline_with_inputs.simulation_results
        == discipline_with_inputs.simulation_results
    )


def test_print_with_inputs(discipline_with_inputs):
    """Test that the method __str__ updates when inputs are defined in the
    discipline."""
    assert discipline.__str__() != discipline_with_inputs.__str__()


def test_print_with_history(discipline_history):
    """Test that the method __str__ updates when history is enabled in the
    discipline."""
    assert discipline.__str__() != discipline_history.__str__()


def test_inputs(discipline, discipline_with_inputs):
    """Test that the input key is present as part of the options when defined in the
    discipline."""
    assert "input" not in discipline._simulate_options.keys()
    assert "input" in discipline_with_inputs._simulate_options.keys()


def test_run_user(discipline):
    """Test that the discipline is correctly ran and returned right values."""
    data = discipline.execute({"f": array([5])})["y"]
    assert pytest.approx(data) == array([35.64729])
