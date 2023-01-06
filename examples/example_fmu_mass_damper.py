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
"""
Create a discipline from a FMU file
===================================
"""
# %%
import sys
from pathlib import Path

import numpy as np
from gemseo_fmu.fmu_discipline import FMUDiscipline

from utils.discipline_plots import plot_discipline_fmu

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform

# %%
# Specify the path to the FMU file
# --------------------------------
# In this example we take a FMU file available in the FMU gallery
fmu_file_path = FMU_DIR_PATH / "Mass_Damper.fmu"

# %%
# Create and instantiate the discipline
# -------------------------------------
# either considering the PyFMI default options
discipline_1 = FMUDiscipline(fmu_file_path, kind="CS")
print(discipline_1)

# %%
# or by changing some simulation options:
options = {
    "start_time": 0.0,
    "final_time": 1.0,
    "algorithm": "FMICSAlg",
    "pyfmi_options": {"ncp": 500},
}

discipline_2 = FMUDiscipline(fmu_file_path, "CS", simulate_options=options)
print(discipline_2)

# %%
# An input function can be provided to the discipline by creating an input object:

# Generate input
# t = np.linspace(0, 10, 100)
# u = np.sin(t)
# data = np.transpose(np.vstack((t, u)))
# input_object = ("f", data)
input_object = ("f", np.sin)

discipline_3 = FMUDiscipline(
    fmu_file_path,
    kind="CS",
    simulate_options={"input": input_object, "start_time": 0, "final_time": 1},
)
print(discipline_3.__repr__())

# %%
# Execute the discipline
# ----------------------
# The discipline can be executed it easily, either considering default inputs:
discipline_1.execute()
discipline_2.execute()

# %%
# or using new inputs:
discipline_3.execute({"mass.m": np.array([1.5]), "spring.c": np.array([1050.0])})

# %%
# The discipline information can be accessed as any other discipline GEMSEO:
print(discipline_1.get_output_data())
print(discipline_2.get_output_data())
print(discipline_3.get_output_data())

# %%
# Access the history of the simulation results
history_results = discipline_3.simulation_results["y"]
print(history_results)

# %%
# Plotting the variables versus time

plot_discipline_fmu(
    discipline_3,
    x_name="time",
    variable_names=["y"],
    x_label="time (seconds)",
    y_label="amplitude (meters)",
    show=True,
)
