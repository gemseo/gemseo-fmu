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
"""A system of static and time-stepping disciplines."""

from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING
from typing import Any

from gemseo import READ_ONLY_EMPTY_DICT
from gemseo.core.discipline import MDODiscipline
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.mda.mda_chain import MDAChain
from numpy import concatenate

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline
from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.utils.time_manager import TimeManager
from gemseo_fmu.utils.time_series import TimeSeries

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from pathlib import Path

    from gemseo.core.discipline_data import DisciplineData

    from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline


class TimeSteppingSystem(MDODiscipline):
    """A system of static and time-stepping disciplines.

    A static discipline computes an output at time $t_k$ from an input at time $t_k$
    while a time-stepping discipline computes an output at time $t_k$ from an input at
    time $t_k$ and its state at time $t_{k-1}$.

    This system co-simulates the disciplines using an MDA-based master algorithm.
    """

    __do_step: bool
    """Whether an execution of the system does a single step.

    Otherwise, do time-stepping until final time.
    """

    __fmu_discipline: list[FMUDiscipline]
    """The FMU disciplines."""

    __restart: bool
    """Whether the system starts from the initial time at each execution."""

    __time_manager: TimeManager
    """The time manager."""

    __mda: MDAChain
    """An MDA chain defining the master algorithm to co-simulate the discipline."""

    def __init__(
        self,
        disciplines: Iterable[str | Path | MDODiscipline],
        final_time: float,
        time_step: float,
        apply_time_step_to_disciplines: bool = True,
        restart: bool = True,
        do_step: bool = False,
        mda_name: str = "MDAJacobi",
        mda_options: Mapping[str, Any] = READ_ONLY_EMPTY_DICT,
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
            mda_name: The MDA class name.
            mda_options: The options of the MDA.
            **fmu_options: The options to instantiate the FMU disciplines.
        """  # noqa: D205 D212 D415
        self.__do_step = do_step
        self.__time_manager = TimeManager(0.0, final_time, time_step)
        self.__restart = restart
        discipline_time_step = time_step if apply_time_step_to_disciplines else 0.0
        all_disciplines = []
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
            all_disciplines.append(discipline)

        all_disciplines.append(AnalyticDiscipline({"time_step_id": "time_step_id+1"}))

        self.__fmu_disciplines = [
            discipline
            for discipline in all_disciplines
            if isinstance(discipline, BaseFMUDiscipline)
        ]
        super().__init__(grammar_type=MDODiscipline.GrammarType.SIMPLER)
        self.__mda = MDAChain(
            all_disciplines,
            inner_mda_name=mda_name,
            # TODO: add max_mda_iter argument when rollback will be available.
            max_mda_iter=0,
            grammar_type=MDODiscipline.GrammarType.SIMPLER,
            **mda_options,
        )
        self.input_grammar.update(self.__mda.input_grammar)
        self.output_grammar.update(self.__mda.output_grammar)

        # Discipline i has priority over discipline i+1 to set the default inputs.
        for discipline in all_disciplines[::-1]:
            self.default_inputs.update({
                input_name: input_value
                for input_name, input_value in discipline.default_inputs.items()
                if input_name in self.input_grammar.names
            })

    def execute(  # noqa: D102
        self, input_data: Mapping[str, Any] = READ_ONLY_EMPTY_DICT
    ) -> DisciplineData:
        if self.__restart:
            self.__mda.default_inputs.update(self.default_inputs)
            self.__time_manager.reset()
            for fmu_discipline in self.__fmu_disciplines:
                fmu_discipline.set_next_execution(restart=True)

            if self.cache is not None:
                self.cache.clear()
                self.__mda.cache.clear()
                for mda in self.__mda.inner_mdas:
                    mda.cache.clear()

        if self.__do_step:
            # At initial time,
            # the default input values are the ``default_inputs``.
            # Afterward,
            # the default input values are the input values from the previous time,
            # which can be found in the local data with get_input_data(),
            # returning an empty dictionary at initial time.
            original_input_data = input_data
            input_data = self.get_input_data() or self.default_inputs
            input_data.update(original_input_data)

        return super().execute(input_data)

    def _run(self) -> None:
        input_data = self.get_input_data()
        if self.__do_step:
            self.__simulate_one_time_step(input_data)
            self.local_data.update(self.__mda.local_data)
        else:
            self.__simulate_to_final_time(input_data)

    def __simulate_one_time_step(self, input_data: Mapping[str, Any]) -> None:
        """Simulate the multidisciplinary system with only one time step."""
        simulation_time = self.__time_manager.update_current_time().step
        for fmu_discipline in self.__fmu_disciplines:
            fmu_discipline.set_next_execution(simulation_time=simulation_time)

        self.__mda.execute(input_data)

    def __simulate_to_final_time(self, input_data: Mapping[str, Any]) -> None:
        """Simulate the multidisciplinary system until final time."""
        local_data_history = []
        while self.__time_manager.remaining > 0:
            self.__simulate_one_time_step(input_data)
            local_data_history.append(copy(self.__mda.local_data))
            input_data = self.__mda.local_data
            for inner_mda in self.__mda.inner_mdas:
                inner_mda.cache.clear()

        # The different time steps are concatenated when the values are NumPy arrays.
        # Given a variable,
        # We suppose that it value type is the same at all time steps.
        local_data_history_0 = local_data_history[0]
        self.store_local_data(**{
            name: concatenate([local_data[name] for local_data in local_data_history])
            for name in local_data_history_0
            if not isinstance(local_data_history_0[name], TimeSeries)
        })
