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
"""Plots for FMUDiscipline."""
import matplotlib.pyplot as plt


def plot_discipline_fmu(
    discipline,
    x_name,
    variable_names=None,
    show=False,
    fig_name=None,
    x_label=None,
    y_label=None,
    title=None,
):
    """Plots the simulation history of a FMUDiscipline.

    Args:
        discipline: the discipline object
        x_name: the history variable name (usually "time")
        variable_names: the variables names to be plotted
        fig_name: The name or path of the Matplotlib figure to be saved or shown
        show: If True, display the Matplotlib figure
        x_label: The text on the x-axis label
        y_label: The text on the y-axis label
        title: The title of  the figure
    """
    var_names = variable_names or discipline.get_input_output_data_names()
    plt.figure(figsize=(30, 20))
    for name in var_names:
        x = discipline.simulation_results[x_name]
        y = discipline.simulation_results[name]
        plt.plot(x, y, label=name)
        plt.legend(loc="upper left")
        plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    if fig_name:
        plt.savefig(fig_name)
    if show:
        plt.show()
