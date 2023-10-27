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
"""The first discipline of the Sellar use case."""
from __future__ import annotations

from cmath import sqrt
from typing import Iterable

import numpy as np
from numpy import array
from numpy import ndarray

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_LOCAL
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_SHARED_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import X_SHARED_2
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_1
from gemseo_fmu.problems.disciplines.sellar.variable_names import Y_2
from gemseo_fmu.problems.fmu_files import get_fmu_file_path


class FMUSellar1(FMUDiscipline):
    """The discipline to compute the coupling variable $y_1$."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            get_fmu_file_path("Sellar1", "sellar"),
            initial_time=0.0,
            final_time=0.0,
            add_time_to_output_grammar=False,
        )

    @staticmethod
    def compute_y_1(x_local: ndarray, x_shared: ndarray, y_2: ndarray) -> complex:
        """Evaluate the first coupling equation in functional form.

        Args:
            x_local: The design variables local to first discipline.
            x_shared: The shared design variables.
            y_2: The coupling variable coming from the second discipline.

        Returns:
            The value of the coupling variable $y_1$.
        """
        return sqrt(x_shared[0] ** 2 + x_shared[1] + x_local[0] - 0.2 * y_2[0])

    def _compute_jacobian(
        self,
        inputs: Iterable[str] | None = None,
        outputs: Iterable[str] | None = None,
    ) -> None:
        self._init_jacobian(inputs, outputs)
        x_local, x_shared_1, x_shared_2, y_2 = self.get_inputs_by_name(
            [X_LOCAL, X_SHARED_1, X_SHARED_2, Y_2]
        )
        x_shared = np.concatenate([x_shared_1, x_shared_2], axis=None)
        denominator_inverse = array([[1.0 / self.compute_y_1(x_local, x_shared, y_2)]])
        self.jac[Y_1] = {
            X_LOCAL: 0.5 * denominator_inverse,
            X_SHARED_1: x_shared[0] * denominator_inverse,
            X_SHARED_2: 0.5 * denominator_inverse,
            Y_2: -0.1 * denominator_inverse,
        }
