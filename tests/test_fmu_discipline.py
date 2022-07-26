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
from pathlib import Path

import pytest
from gemseo_fmu.fmu_discipline import FMUDiscipline
from numpy import array
from pyfmi.fmi import FMUException

# Test FMU file (Mass_Damper)
FMU_FILE_PATH = Path(__file__).parent.parent / "fmu_files/Mass_Damper.fmu"


@pytest.fixture()
def discipline() -> FMUDiscipline:
    """Return a FMUDiscipline object."""
    return FMUDiscipline(FMU_FILE_PATH, kind="CS")


# Model causality (Parameter=0, Calculated Parameter=1, Input=2, Output=3, Local=4,
# Independent=5, Unknown=6)
PARAMETERS_0 = {
    "damper.d": array([10.0]),
    "damper.s_nominal": array([0.0001]),
    "fixed.s0": array([1.0]),
    "mass.L": array([1.0]),
    "mass.m": array([1.0]),
    "spring.c": array([10000.0]),
    "spring.s_rel0": array([1.0]),
}

CALCULATED_PARAMETERS_1 = {
    "damper.flange_b.s": array([0.0]),
    "fixed.flange.s": array([0.0]),
    "spring.flange_b.s": array([0.0]),
    "damper.stateSelect": array([0]),
    "mass.stateSelect": array([0]),
    "damper.useHeatPort": array([False]),
    "force.useSupport": array([False]),
}
INPUT_VARIABLES_2 = {"f": array([0.0])}
OUTPUT_VARIABLES_3 = {"y": array([0.5])}
LOCAL_VARIABLES_4 = {
    "damper.s_rel": array([0.0]),
    "damper.v_rel": array([0.0]),
    "der(damper.s_rel)": array([0.0]),
    "der(damper.v_rel)": array([10000.0]),
    "der(der(mass.flange_b.s))": array([-10000.0]),
    "der(mass.flange_b.s)": array([-0.0]),
    "der(mass.s)": array([-0.0]),
    "der(mass.v)": array([-10000.0]),
    "damper.f": array([0.0]),
    "damper.lossPower": array([0.0]),
    "fixed.flange.f": array([10000.0]),
    "force.s": array([0.0]),
    "force.s_support": array([0.0]),
    "mass.a": array([-10000.0]),
    "mass.flange_b.f": array([-10000.0]),
    "mass.flange_b.s": array([1.0]),
    "mass.s": array([0.5]),
    "mass.v": array([-0.0]),
    "spring.f": array([-10000.0]),
    "spring.s_rel": array([0.0]),
    "damper.flange_a.f": array([-0.0]),
    "damper.flange_a.s": array([1.0]),
    "damper.flange_b.f": array([0.0]),
    "force.f": array([0.0]),
    "force.flange.f": array([-0.0]),
    "force.flange.s": array([0.0]),
    "mass.flange_a.f": array([0.0]),
    "mass.flange_a.s": array([0.0]),
    "spring.flange_a.f": array([10000.0]),
    "spring.flange_a.s": array([1.0]),
    "spring.flange_b.f": array([-10000.0]),
}
INDEPENDENT_VARIABLES_5 = {}
UNKNOWN_VARIABLES_6 = {}


def test_fmu_kind(discipline):
    """Tests if the model is either of type Model Exchange or Co-Simulation."""
    assert discipline.kind in ("ME", "CS")


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


def test_variables_values_by_causality(discipline):
    """Test variable values by causality."""
    assert discipline._parameters == PARAMETERS_0
    assert discipline._calculated_parameters == CALCULATED_PARAMETERS_1
    assert discipline._input_variables == INPUT_VARIABLES_2
    assert discipline._output_variables == OUTPUT_VARIABLES_3
    assert discipline._local_variables == LOCAL_VARIABLES_4
    assert discipline._independent_variables == INDEPENDENT_VARIABLES_5
    assert discipline._unknown_variables == UNKNOWN_VARIABLES_6


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
        FMUDiscipline(FMU_FILE_PATH, kind="CS", simulate_options=options)


def test_run_user(discipline):
    """Test that the discipline is correctly ran and returned right values."""
    data = discipline.execute({"f": array([5])})["y"]
    print(data)
    assert pytest.approx(data) == array([71.83026655])
