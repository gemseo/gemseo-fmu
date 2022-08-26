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
from pyfmi.fmi import FMUException

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform


def _discipline(file_name: str = "Mass_Damper.fmu", **kwargs: Any) -> FMUDiscipline:
    return FMUDiscipline(FMU_DIR_PATH / file_name, kind="CS", **kwargs)


discipline = pytest.fixture(_discipline)


def test_fmu_kind(discipline):
    """Tests if the model is either of type Model Exchange or Co-Simulation."""
    assert discipline._kind in ("ME", "CS")


def test_inputs_names_from_fmu(discipline):
    """Test input variables read from fmu file.

    GEMSEO input grammar is defined from FMU model causalities 0 and 2 (i.e. the FMU
    parameters and FMU input variables)
    """
    assert discipline.get_input_data_names() == {
        "f",
        "damper.d",
        "damper.s_nominal",
        "fixed.s0",
        "mass.L",
        "mass.m",
        "spring.c",
        "spring.s_rel0",
    }


def test_outputs_names_from_fmu(discipline):
    """Test output variables read from fmu file; GEMSEO output grammar is defined from
    FMU model causalities 1 (i.e. the FMU output variables)"""
    assert discipline.get_output_data_names() == {"y"}


def test_raises_fmu_file_not_provided(discipline):
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
        "options": {"ncp": 510, "initialize": True, "not_a_simulation_option": None},
    }
    msg = (
        "Not a PyFMI simulation option. "
        "Use the method get_available_simulate_options to get a list of "
        "available options"
    )

    with pytest.raises(ValueError, match=msg):
        _discipline(simulate_options=options)


def test_run_user(discipline):
    """Test that the discipline is correctly ran and returned right values."""
    data = discipline.execute({"f": array([5])})["y"]
    assert pytest.approx(data) == array([35.64729])
