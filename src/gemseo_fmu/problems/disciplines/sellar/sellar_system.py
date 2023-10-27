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
"""The system discipline of the Sellar use case."""
from __future__ import annotations

from cmath import exp
from typing import Iterable

from numpy import array
from numpy import ndarray
from numpy import ones

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.problems.disciplines.sellar.variable_names import C_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import C_2
from gemseo_fmu.problems.disciplines.sellar.variable_names import OBJ
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_LOCAL
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_SHARED_2
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_2
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


class FMUSellarSystem(FMUDiscipline):
    """The discipline to compute the objective and constraints of the Sellar problem."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            get_fmu_file_path("SellarSystem", "sellar"),
            initial_time=0.0,
            final_time=0.0,
            add_time_to_output_grammar=False,
        )

    @staticmethod
    def compute_obj(
        x_local: ndarray,
        x_shared: ndarray,
        y_1: ndarray,
        y_2: ndarray,
    ) -> float:
        """Evaluate the objective $obj$.

        Args:
            x_local: The design variables local to the first discipline.
            x_shared: The shared design variables.
            y_1: The coupling variable coming from the first discipline.
            y_2: The coupling variable coming from the second discipline.

        Returns:
            The value of the objective $obj$.
        """
        return x_local[0] ** 2 + x_shared[1] + y_1[0] ** 2 + exp(-y_2[0])

    @staticmethod
    def compute_c_1(
        y_1: ndarray,
    ) -> float:
        """Evaluate the constraint $c_1$.

        Args:
            y_1: The coupling variable coming from the first discipline.

        Returns:
            The value of the constraint $c_1$.
        """
        return 3.16 - y_1[0] ** 2

    @staticmethod
    def compute_c_2(
        y_2: ndarray,
    ) -> float:
        """Evaluate the constraint $c_2$.

        Args:
            y_2: The coupling variable coming from the second discipline.

        Returns:
            The value of the constraint $c_2$.
        """
        return y_2[0] - 24.0

    def _compute_jacobian(
        self,
        inputs: Iterable[str] | None = None,
        outputs: Iterable[str] | None = None,
    ) -> None:
        self._init_jacobian(inputs, outputs)
        x_local, y_1, y_2 = self.get_inputs_by_name([X_LOCAL, Y_1, Y_2])
        y_10 = y_1[0]
        self.jac[C_1][Y_1] = array([[-2.0 * y_10]])
        self.jac[C_2][Y_2] = ones((1, 1))
        self.jac[OBJ] = {
            X_LOCAL: array([[2.0 * x_local[0]]]),
            X_SHARED_2: ones((1, 1)),
            Y_1: array([[2.0 * y_10]]),
            Y_2: array([[-exp(-y_2[0])]]),
        }
