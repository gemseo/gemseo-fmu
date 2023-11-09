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
#    INITIAL AUTHORS - API and implementation and/or documentation
#        :author: Jorge Camacho
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""The second discipline of the Sellar use case."""
from __future__ import annotations

from typing import Iterable

from numpy import ndarray
from numpy import ones
from numpy import sign
from numpy import zeros

from gemseo_fmu.disciplines.static_fmu_discipline import StaticFMUDiscipline
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_SHARED_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_SHARED_2
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_2
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


class FMUSellar2(StaticFMUDiscipline):
    """The discipline to compute the coupling variable $y_2$."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(get_fmu_file_path("Sellar2", "sellar"))

    def _compute_jacobian(
        self,
        inputs: Iterable[str] | None = None,
        outputs: Iterable[str] | None = None,
    ) -> None:
        self._init_jacobian(inputs, outputs)
        y_1 = self.get_inputs_by_name(Y_1)
        self.jac[Y_2] = {
            X_SHARED_1: ones((1, 1)),
            X_SHARED_2: ones((1, 1)),
            Y_1: sign(y_1[0]) * zeros((1, 1)),
        }

    @staticmethod
    def compute_y_2(
        x_shared: ndarray,
        y_1: ndarray,
    ) -> float:
        """Evaluate the second coupling equation in functional form.

        Args:
            x_shared: The shared design variables.
            y_1: The coupling variable coming from the first discipline.

        Returns:
            The value of the coupling variable $y_2$.
        """
        out = x_shared[0] + x_shared[1]
        y_10 = y_1[0]
        if y_10.real == 0:
            return out
        if y_10.real > 0:
            return out + y_10
        return out - y_10
