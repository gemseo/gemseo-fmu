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

from gemseo.core._process_flow.base_process_flow import BaseProcessFlow
from gemseo.core.coupling_structure import CouplingStructure
from gemseo.core.discipline.discipline import Discipline
from gemseo.mda.mda_chain import MDAChain
from gemseo.utils.constants import READ_ONLY_EMPTY_DICT
from numpy import atleast_1d
from numpy import concatenate

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline
from gemseo_fmu.disciplines.do_step_fmu_discipline import DoStepFMUDiscipline
from gemseo_fmu.utils.time_manager import TimeManager
from gemseo_fmu.utils.time_series import TimeSeries

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from pathlib import Path

    from gemseo.core._base_monitored_process import BaseMonitoredProcess
    from gemseo.core._process_flow.execution_sequences.loop import LoopExecSequence
    from gemseo.core.discipline.discipline import DisciplineData
    from gemseo.typing import StrKeyMapping

    from gemseo_fmu.disciplines.fmu_discipline import FMUDiscipline


class _TimeSteppingSystemProcessFlow(BaseProcessFlow):
    """The process flow of a time stepping system."""

    def get_data_flow(
        self,
    ) -> list[tuple[Discipline, Discipline, list[str]]]:
        return self._node.mda.get_process_flow().get_data_flow()

    def get_execution_flow(self) -> LoopExecSequence:
        return self._node.mda.get_process_flow().get_execution_flow()

    def get_disciplines_in_data_flow(self) -> list[BaseMonitoredProcess]:
        return [self._node]


class TimeSteppingSystem(Discipline):
    """A system of static and time-stepping disciplines.

    A static discipline computes an output at time $t_k$ from an input at time $t_k$
    while a time-stepping discipline computes an output at time $t_k$ from an input at
    time $t_k$ and its state at time $t_{k-1}$.

    This system co-simulates the disciplines using an MDA-based master algorithm.
    """

    default_grammar_type = Discipline.GrammarType.SIMPLER

    __do_step: bool
    """Whether an execution of the system does a single step.

    Otherwise, do time-stepping until final time.
    """

    __fmu_discipline: list[FMUDiscipline]
    """The FMU disciplines."""

    __mda: MDAChain
    """The MDA defining the master algorithm to co-simulate the discipline."""

    __mda_max_iter_at_t0: int
    """ The maximum number of iterations of the MDA algorithm at initial time."""

    __restart: bool
    """Whether the system starts from the initial time at each execution."""

    __time_manager: TimeManager
    """The time manager."""

    _process_flow_class = _TimeSteppingSystemProcessFlow

    def __init__(
        self,
        disciplines: Iterable[str | Path | Discipline],
        final_time: float,
        time_step: float,
        apply_time_step_to_disciplines: bool = True,
        restart: bool = True,
        do_step: bool = False,
        mda_name: str = "MDAJacobi",
        mda_options: Mapping[str, Any] = READ_ONLY_EMPTY_DICT,
        mda_max_iter_at_t0: int = 0,
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
            mda_max_iter_at_t0: The maximum number of iterations of the MDA algorithm
                at initial time, to find a multidisciplinary feasible configuration.
            **fmu_options: The options to instantiate the FMU disciplines.
        """  # noqa: D205 D212 D415
        self.__do_step = do_step
        self.__time_manager = TimeManager(0.0, final_time, time_step)
        self.__restart = restart
        self.__mda_max_iter_at_t0 = mda_max_iter_at_t0
        discipline_time_step = time_step if apply_time_step_to_disciplines else 0.0
        all_disciplines = []
        for discipline in disciplines:
            if isinstance(discipline, DoStepFMUDiscipline):
                discipline.set_default_execution(
                    final_time=final_time,
                    restart=False,
                    time_step=discipline_time_step or None,
                )
            elif isinstance(discipline, BaseFMUDiscipline):
                discipline.set_default_execution(
                    final_time=final_time,
                    restart=False,
                    do_step=True,
                    time_step=discipline_time_step or None,
                )
            elif not isinstance(discipline, Discipline):
                discipline = DoStepFMUDiscipline(
                    discipline,
                    time_step=discipline_time_step,
                    final_time=final_time,
                    **fmu_options,
                )
            all_disciplines.append(discipline)

        self.__fmu_disciplines = [
            discipline
            for discipline in all_disciplines
            if isinstance(discipline, BaseFMUDiscipline)
        ]
        super().__init__()
        strong_couplings = CouplingStructure(all_disciplines).strong_couplings
        for fmu_discipline in self.__fmu_disciplines:
            input_grammar = fmu_discipline.input_grammar
            array_strong_couplings = set()
            for strong_coupling in strong_couplings:
                if strong_coupling in input_grammar:
                    array_strong_couplings.add(strong_coupling)

            input_grammar.update_from_names(array_strong_couplings)

        self.__mda = MDAChain(
            all_disciplines,
            inner_mda_name=mda_name,
            # TODO: add max_mda_iter argument when rollback will be available.
            max_mda_iter=0,
            inner_mda_settings=mda_options,
        )
        for mda in self.__mda.inner_mdas:
            mda.settings.max_mda_iter = 0

        # TimeSteppingSystem uses an MDA
        # to co-simulate from t(k) to t(k+1) and
        # to iterate at t(0) to find a multidisciplinary starting state.
        # If the coupled system is an n-order ODE, with n > 1,
        # the coupling vector can remain constant during one iteration
        # before changing at the next iteration.
        # For this reason, we need to disable the caches.
        cache_type = self.__mda.CacheType.NONE
        self.__mda.set_cache(cache_type)
        self.__mda.mdo_chain.set_cache(cache_type)
        for mda in self.__mda.inner_mdas:
            mda.set_cache(cache_type)

        self.input_grammar.update(self.__mda.input_grammar)
        self.output_grammar.update(self.__mda.output_grammar)

        # Discipline i has priority over discipline i+1 to set the default inputs.
        for discipline in all_disciplines[::-1]:
            self.default_input_data.update({
                input_name: input_value
                for input_name, input_value in discipline.default_input_data.items()
                if input_name in self.input_grammar.names
            })

    @property
    def mda(self) -> MDAChain:
        """The MDA defining the master algorithm to co-simulate the discipline."""
        return self.__mda

    def execute(  # noqa: D102
        self, input_data: Mapping[str, Any] = READ_ONLY_EMPTY_DICT
    ) -> DisciplineData:
        if self.__restart:
            self.__mda.default_input_data.update(self.default_input_data)
            self.__time_manager.reset()
            for fmu_discipline in self.__fmu_disciplines:
                fmu_discipline.set_next_execution(restart=True)

            if self.cache is not None:
                self.cache.clear()

        if self.__do_step:
            # At initial time,
            # the default input values are the ``default_inputs``.
            # Afterward,
            # the default input values are the input values from the previous time,
            # which can be found in the local data with get_input_data(),
            # returning an empty dictionary at initial time.
            original_input_data = input_data
            input_data = self.get_input_data() or self.default_input_data
            input_data.update(original_input_data)

        return super().execute(input_data)

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        if self.__time_manager.is_initial and self.__mda_max_iter_at_t0 > 0:
            max_mda_iter = self.__mda.settings.max_mda_iter
            for mda in self.__mda.inner_mdas:
                mda.settings.max_mda_iter = self.__mda_max_iter_at_t0

            for fmu_discipline in self.__fmu_disciplines:
                fmu_discipline.set_default_execution(initialize_only=True)

            self.__mda.execute()
            for mda in self.__mda.inner_mdas:
                mda.settings.max_mda_iter = max_mda_iter

            for fmu_discipline in self.__fmu_disciplines:
                fmu_discipline.set_default_execution(
                    initialize_only=False, use_arrays_only=True
                )

        input_data = dict(input_data)
        input_data.update(self.__mda.io.data)
        if self.__do_step:
            self.__simulate_one_time_step(input_data)
            self.io.data.update(self.__mda.io.data)
        else:
            self.__simulate_to_final_time(input_data)

    def __simulate_one_time_step(self, input_data: Mapping[str, Any]) -> None:
        """Simulate the multidisciplinary system with only one time step."""
        _, _, simulation_time = self.__time_manager.update_current_time(
            return_time_manager=False
        )
        for fmu_discipline in self.__fmu_disciplines:
            fmu_discipline.set_next_execution(simulation_time=simulation_time)

        self.__mda.execute(input_data)

    def __simulate_to_final_time(self, input_data: Mapping[str, Any]) -> None:
        """Simulate the multidisciplinary system until final time."""
        local_data_history = []
        while self.__time_manager.remaining > 0:
            self.__simulate_one_time_step(input_data)
            local_data_history.append(copy(self.__mda.io.data))
            input_data = self.__mda.io.data

        # The different time steps are concatenated when the values are NumPy arrays.
        # Given a variable,
        # We suppose that its value type is the same at all time steps.
        self.io.update_output_data({
            name: concatenate([
                atleast_1d(local_data[name]) for local_data in local_data_history
            ])
            for name, initial_value in local_data_history[0].items()
            if not isinstance(initial_value, TimeSeries)
        })
