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
"""A system of disciplines based on static and time-stepping disciplines."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Final

from gemseo.core.chain import MDOParallelChain
from gemseo.core.discipline import MDODiscipline
from numpy import array
from numpy import concatenate

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline
from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from pathlib import Path

    from gemseo.core.discipline_data import DisciplineData
    from gemseo.typing import IntegerArray

    from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline


class TimeSteppingSystem(MDOParallelChain):
    """A system of static and time-stepping disciplines.

    A static discipline computes an output at time $t_k$ from an input at time $t_k$
    while a time-stepping discipline computes an output at time $t_k$ from an input at
    time $t_k$ and its state at time $t_{k-1}$.

    At each time step, the time-stepping system executes such disciplines one after the
    other.
    """

    __current_time: float
    """The current time."""

    __do_step: bool
    """Whether an execution of the system does a single step.

    Otherwise, do time-stepping until final time.
    """

    __final_time: float
    """The final time."""

    __fmu_discipline: list[FMUDiscipline]
    """The FMU disciplines."""

    __initial_time: float
    """The initial time."""

    __restart: bool
    """Whether the system starts from the initial time at each execution."""

    __time_step: float
    """The time step of the system."""

    __time_step_id: IntegerArray
    """The identifier of the time step."""

    __TIME_STEP_ID_LABEL: Final[str] = "time_step_id"
    """The label for the identifier of the time step."""

    def __init__(
        self,
        disciplines: Iterable[str | Path | MDODiscipline],
        final_time: float,
        time_step: float,
        apply_time_step_to_disciplines: bool = True,
        restart: bool = True,
        do_step: bool = False,
        **fmu_options: Any,
    ) -> None:
        """
        Args:
            disciplines: The static and time-stepping disciplines.
                The disciplines will be executed circularly
                according to the order of their definition.
            final_time: The final time of the simulation
                (the initial time is 0).
            time_step: The time step of the system.
            apply_time_step_to_disciplines: Whether the time-stepping disciplines
                should use `time_step` as time step. Otherwise, their own time steps.
            restart: Whether the system is restarted at initial time
                after each  execution.
            do_step: Whether the model is simulated over only one `time_step`
                when calling the execution method.
                Otherwise, simulate the model from initial time to `final_time`.
            **fmu_options: The options to instantiate the FMU disciplines.
        """  # noqa: D205 D212 D415
        self.__do_step = do_step
        self.__current_time = self.__initial_time = 0.0
        self.__final_time = final_time
        self.__restart = restart
        self.__time_step = time_step
        discipline_time_step = time_step if apply_time_step_to_disciplines else 0.0
        _disciplines = []
        for discipline in disciplines:
            if isinstance(discipline, BaseFMUDiscipline):
                discipline.set_default_execution(
                    final_time=final_time,
                    restart=False,
                    do_step=True,
                    time_step=discipline_time_step or None,
                )
            elif not isinstance(discipline, MDODiscipline):
                discipline = DoStepFMUDiscipline(
                    discipline,
                    time_step=discipline_time_step,
                    final_time=final_time,
                    **fmu_options,
                )
            _disciplines.append(discipline)

        self.__fmu_disciplines = [
            discipline
            for discipline in _disciplines
            if isinstance(discipline, BaseFMUDiscipline)
        ]
        super().__init__(_disciplines, grammar_type=MDODiscipline.GrammarType.SIMPLER)
        if self.__do_step:
            # Workaround to be replaced by something related to time step.
            self.__time_step_id = array([0])
            self.input_grammar.update_from_names([self.__TIME_STEP_ID_LABEL])

        # Discipline i has priority over discipline i+1 to set the default inputs.
        self.default_inputs.clear()
        for discipline in self.disciplines[::-1]:
            self.default_inputs.update({
                input_name: input_value
                for input_name, input_value in discipline.default_inputs.items()
                if input_name in self.input_grammar.names
            })
        self.__original_default_inputs = self.default_inputs.copy()

    def execute(  # noqa: D102
        self, input_data: Mapping[str, Any] | None = None
    ) -> DisciplineData:
        if self.__restart:
            self.default_inputs = self.__original_default_inputs.copy()
            self.__current_time = self.__initial_time
            self.__time_step_id = array([0])
            for discipline in self.__fmu_disciplines:
                discipline.set_next_execution(restart=True)

            if self.cache is not None:
                self.cache.clear()

        if self.__do_step:
            input_data = input_data or {}
            self.__time_step_id = self.__time_step_id + 1
            input_data[self.__TIME_STEP_ID_LABEL] = self.__time_step_id

        return super().execute(input_data)

    def _run(self) -> None:
        if self.__do_step:
            self.__simulate_one_time_step()
            self.default_inputs.update(self.get_input_data())
        else:
            self.__simulate_to_final_time()

    def __simulate_one_time_step(self) -> None:
        """Simulate the multidisciplinary system with only one time step."""
        time_step = min(self.__final_time - self.__current_time, self.__time_step)
        if time_step <= 0:
            msg = (
                "The time stepping system cannot be executed as "
                f"its current time is its final time ({self.__final_time})."
            )
            raise ValueError(msg)

        for discipline in self.__fmu_disciplines:
            discipline.set_next_execution(simulation_time=time_step)
        super()._run()
        self.__current_time += time_step

    def __simulate_to_final_time(self) -> None:
        """Simulate the multidisciplinary system until final time."""
        local_data_history = []
        while self.__current_time < self.__final_time:
            self.__simulate_one_time_step()
            local_data_history.append(self.local_data.copy())

        self.store_local_data(**{
            name: concatenate([local_data[name] for local_data in local_data_history])
            for name in local_data_history[0]
        })
