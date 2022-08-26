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
# Copyright 2021 IRT Saint ExupÃ©ry, https://www.irt-saintexupery.com
#
# This work is licensed under a BSD 0-Clause License.
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or initial documentation
#        :author: Jorge CAMACHO CASERO
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""Comparing sensitivity indices."""
import sys
from pathlib import Path

from gemseo.algos.parameter_space import ParameterSpace
from gemseo.uncertainty.sensitivity.correlation.analysis import CorrelationAnalysis
from gemseo.uncertainty.sensitivity.morris.analysis import MorrisAnalysis
from gemseo_fmu.fmu_discipline import FMUDiscipline
from matplotlib import pyplot as plt
from numpy import pi

FMU_DIR_PATH = Path(__file__).parent.parent / "fmu_files" / sys.platform


#######################################################################################
# In this example,
# we consider the Ishigami function:
#
# .. math::
#
#    Y=\sin(X_1)+7\sin(X_2)^2+0.1*X_3^4\sin(X_1)
#
# whose description is contained in the FMU file created from the Modelica code below:

# model IshigamiFunction
#   parameter Real x1 = 0;
#   parameter Real x2 = 0;
#   parameter Real x3 = 0;
#   output Real y;
# equation
#   y = sin(x1) + 7 * sin(x2)^2 + 0.1 * x3^4 * sin(x1);
# end IshigamiFunction;
discipline = FMUDiscipline(FMU_DIR_PATH / "IshigamiFunction.fmu", kind="CS")

#######################################################################################
# The different uncertain variables :math:`X_1` , :math:`X_2` and :math:`X_3`
# are independent and identically distributed
# according to an uniform distribution between :math:`-\pi` and :math:`\pi`:
space = ParameterSpace()
for variable in ["x1", "x2", "x3"]:
    space.add_random_variable(
        variable, "OTUniformDistribution", minimum=-pi, maximum=pi
    )

#######################################################################################
# We would like to carry out two sensitivity analyses,
# e.g. a first one based on correlation coefficients
# and a second one based on the Morris methodology,
# and compare the results,
#
# Firstly,
# we create a :class:`.CorrelationAnalysis`
# and compute the sensitivity indices:
correlation = CorrelationAnalysis([discipline], space, 10)
correlation.compute_indices()

#######################################################################################
# Then, we create a GEMSEO class MorrisAnalysis and compute the sensitivity indices:
morris = MorrisAnalysis([discipline], space, 10)
morris.compute_indices()

#######################################################################################
# Lastly, we compare these analyses either using a bar chart:
morris.plot_comparison(correlation, "y", use_bar_plot=True, save=False)

#######################################################################################
# or a radar plot:
morris.plot_comparison(correlation, "y", use_bar_plot=False, save=False)
# Workaround for HTML rendering, instead of ``show=True``
plt.show()
