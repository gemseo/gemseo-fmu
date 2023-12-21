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
"""An FMU discipline whose execution simulates only one time step."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class DoStepFMUDiscipline(FMUDiscipline):
    """An FMU discipline whose execution simulates only one time step."""

    def __init__(  # noqa: D107
        self,
        file_path: str | Path,
        input_names: Iterable[str] | None = (),
        output_names: Iterable[str] = (),
        initial_time: float | None = None,
        final_time: float | None = None,
        time_step: float = 0.0,
        add_time_to_output_grammar: bool = True,
        restart: bool = False,
        name: str = "",
        solver_name: FMUDiscipline.Solver = FMUDiscipline.Solver.CVODE,
        fmu_instance_directory: str | Path = "",
        delete_fmu_instance_directory: bool = True,
        **pre_instantiation_parameters: Any,
    ) -> None:
        do_step = pre_instantiation_parameters.get(self._DO_STEP, None)
        if do_step is False:
            raise ValueError("DoStepFMUDiscipline has no do_step parameter.")

        if do_step is True:
            del pre_instantiation_parameters[self._DO_STEP]

        super().__init__(
            file_path,
            input_names=input_names,
            output_names=output_names,
            initial_time=initial_time,
            final_time=final_time,
            time_step=time_step,
            add_time_to_output_grammar=add_time_to_output_grammar,
            restart=restart,
            do_step=True,
            name=name,
            use_co_simulation=True,
            solver_name=solver_name,
            fmu_instance_directory=fmu_instance_directory,
            delete_fmu_instance_directory=delete_fmu_instance_directory,
            **pre_instantiation_parameters,
        )
