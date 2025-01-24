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
"""A base discipline wrapping a Functional Mockup Unit (FMU) model."""

from __future__ import annotations

import logging
from copy import copy
from pathlib import Path
from shutil import rmtree
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Union

from fmpy import extract
from fmpy import instantiate_fmu
from fmpy import read_model_description
from fmpy import simulate_fmu
from fmpy.fmi1 import FMU1Model
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Model
from fmpy.fmi2 import FMU2Slave
from fmpy.fmi3 import FMU3Model
from fmpy.fmi3 import FMU3Slave
from fmpy.util import fmu_info
from gemseo.core.discipline.discipline import Discipline
from gemseo.utils.constants import READ_ONLY_EMPTY_DICT
from gemseo.utils.pydantic_ndarray import NDArrayPydantic
from numpy import append
from numpy import array
from numpy import ndarray
from strenum import StrEnum

from gemseo_fmu.utils.time_duration import TimeDuration
from gemseo_fmu.utils.time_manager import TimeManager
from gemseo_fmu.utils.time_series import TimeSeries

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from fmpy.model_description import DefaultExperiment
    from fmpy.model_description import ModelDescription
    from fmpy.simulation import Recorder
    from gemseo.core.discipline_data import DisciplineData
    from gemseo.typing import NumberArray
    from gemseo.typing import RealArray
    from gemseo.typing import StrKeyMapping

    from gemseo_fmu.utils.time_duration import TimeDurationType

FMUModel = Union[FMU1Model, FMU2Model, FMU3Model, FMU1Slave, FMU2Slave, FMU3Slave]

LOGGER = logging.getLogger(__name__)


class BaseFMUDiscipline(Discipline):
    """A base discipline wrapping a Functional Mockup Unit (FMU) model.

    This discipline relies on [FMPy](https://github.com/CATIA-Systems/FMPy).
    """

    default_grammar_type = Discipline.GrammarType.PYDANTIC
    default_cache_type = Discipline.CacheType.NONE

    class Solver(StrEnum):
        """The solver to simulate a model-exchange model."""

        EULER = "Euler"
        CVODE = "CVode"

    class _Causality(StrEnum):
        """The causality of an FMU variable."""

        INPUT = "input"
        OUTPUT = "output"
        PARAMETER = "parameter"

    _CO_SIMULATION: Final[str] = "CoSimulation"
    _DO_STEP: Final[str] = "do_step"
    _FINAL_TIME: Final[str] = "final_time"
    _INITIAL_TIME: Final[str] = "initial_time"
    _INPUT: Final[str] = _Causality.INPUT
    _MODEL_EXCHANGE: Final[str] = "ModelExchange"
    _PARAMETER: Final[str] = _Causality.PARAMETER
    _RESTART: Final[str] = "restart"
    _SIMULATION_TIME: Final[str] = "simulation_time"
    _TIME: Final[str] = "time"
    _TIME_STEP: Final[str] = "time_step"

    _WARN_ABOUT_ZERO_TIME_STEP: ClassVar[bool] = True
    """Whether to log a warning message when the time step is zero."""

    _initial_values: dict[str, NumberArray]
    """The initial values of the discipline outputs."""

    __causalities_to_variable_names: dict[str, list[str]]
    """The names of the variables sorted by causality."""

    __default_simulation_settings: dict[str, bool | float]
    """The default values of the simulation settings."""

    __delete_model_instance_directory: bool
    """Whether trying to delete the directory of the FMU instance when deleting the
    discipline."""

    __do_step: bool
    """Whether the discipline is executed step by step."""

    __executed: bool
    """Whether the discipline has already been executed."""

    __file_path: Path
    """The path to the FMU file, which is a ZIP archive."""

    __fmu_output_names: tuple[str]
    """The names of the FMU model outputs used by the discipline."""

    __from_fmu_names: dict[str, str]
    """The map from the FMU variable names to the discipline variable names."""

    __parameter_getter_name: str
    """The name of the FMU method to get a parameter."""

    __model: FMUModel
    """The FMU model."""

    __model_description: ModelDescription
    """The description of the FMU model."""

    __model_dir_path: Path
    """The description of the FMU model, read from the XML file in the archive."""

    __model_fmi_version: str
    """The FMI version of the FMU model."""

    __model_name: str
    """The name of the FMU model."""

    __names_to_references: dict[str, int]
    """The value references bound to the variables names."""

    __names_to_time_functions: dict[str, Callable[[TimeDurationType], float]]
    """The input names bound to the time functions at the last execution."""

    __parameter_setter_name: str
    """The name of the FMU method to set a parameter."""

    __simulation_settings: dict[str, bool | float]
    """The values of the simulation settings."""

    __solver_name: str
    """The name of the ODE solver."""

    __time: RealArray | None
    """The time steps of the last execution; `None` when not yet executed."""

    __time_manager: TimeManager
    """The time manager."""

    __to_fmu_names: dict[str, str]
    """The map from the discipline variable names to the FMU variable names."""

    __use_fmi_3: bool
    """Whether the FMU model is based on FMI 3.0."""

    def __init__(
        self,
        file_path: str | Path,
        input_names: Iterable[str] | None = (),
        output_names: Iterable[str] = (),
        initial_time: TimeDurationType | None = None,
        final_time: TimeDurationType | None = None,
        time_step: TimeDurationType = 0.0,
        add_time_to_output_grammar: bool = True,
        restart: bool = True,
        do_step: bool = False,
        name: str = "",
        use_co_simulation: bool = True,
        solver_name: Solver = Solver.CVODE,
        model_instance_directory: str | Path = "",
        delete_model_instance_directory: bool = True,
        variable_names: Mapping[str, str] = READ_ONLY_EMPTY_DICT,
        **pre_instantiation_parameters: Any,
    ) -> None:
        """
        Args:
            file_path: The path to the FMU model file.
            input_names: The names of the FMU model inputs;
                if empty, use all the inputs and parameters of the FMU model;
                if `None`, do not use inputs.
            output_names: The names of the FMU model outputs.
                if empty, use all the outputs of the FMU model.
            initial_time: The initial time of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                if `None`, use the start time defined in the FMU model if any;
                otherwise use 0.
            final_time: The final time of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                if `None`, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
            time_step: The time step of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                if `0.`, use the stop time defined in the FMU model if any;
                otherwise use `0.`.
            add_time_to_output_grammar: Whether the time is added to the output grammar.
            restart: Whether the model is restarted at `initial_time` after execution.
            do_step: Whether the model is simulated over only one `time_step`
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            use_co_simulation: Whether the co-simulation FMI type is used.
                Otherwise, use model-exchange FMI type.
                When `do_step` is `True`, the co-simulation FMI type is required.
            solver_name: The name of the solver to simulate a model-exchange model.
            model_instance_directory: The directory of the FMU instance,
                containing the files extracted from the FMU model file;
                if empty, let `fmpy` create a temporary directory.
            delete_model_instance_directory: Whether to delete the directory
                of the FMU instance when deleting the discipline.
            variable_names: The names of the discipline inputs and outputs
                associated with the names of the FMU model inputs and outputs,
                passed as `{fmu_model_variable_name: discipline_variable_name, ...}`.
                When missing, use the names of the FMU model inputs and outputs.
            **pre_instantiation_parameters: The parameters to be passed
                to `_pre_instantiate()`.
        """  # noqa: D205 D212 D415
        self.__delete_model_instance_directory = delete_model_instance_directory
        self.__executed = False
        self.__names_to_time_functions = {}
        self.__solver_name = str(solver_name)
        self.name = self.__set_fmu_model(
            file_path, model_instance_directory, do_step, use_co_simulation, name
        )
        self.__from_fmu_names = dict(variable_names)
        self.__to_fmu_names = {v: k for k, v in variable_names.items()}
        self.__from_fmu_names[self._TIME] = self.__to_fmu_names[self._TIME] = self._TIME
        input_names, output_names = (
            self.__set_variable_names_references_and_causalities(
                input_names, output_names
            )
        )
        self.__set_initial_values()
        self.__set_time(initial_time, final_time, time_step, do_step, restart)
        self._pre_instantiate(**(pre_instantiation_parameters or {}))
        super().__init__(name=self.name)

        self.input_grammar.update_from_types(
            dict.fromkeys(input_names, Union[int, float, NDArrayPydantic, TimeSeries])
        )
        self.output_grammar.update_from_names(output_names)
        if add_time_to_output_grammar:
            self.output_grammar.update_from_types({
                self._TIME: Union[float, NDArrayPydantic[float]]
            })
            self.output_grammar.add_namespace(self._TIME, self.name)

        self.default_input_data = {
            input_name: self._initial_values[input_name] for input_name in input_names
        }

    def __set_time(
        self,
        initial_time: TimeDurationType | None,
        final_time: TimeDurationType | None,
        time_step: TimeDurationType,
        do_step: bool,
        restart: bool,
    ) -> None:
        """Set all about time.

        Args:
            initial_time: The initial time of the simulation;
                if `None`, use the start time defined in the FMU model if any;
                otherwise use 0.
            final_time: The final time of the simulation;
                if `None`, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
            time_step: The time step of the simulation.
                If `0.`, it is computed by the wrapped library `fmpy`.
            do_step: Whether the model is simulated over only one `time_step`
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            restart: Whether the model is restarted at `initial_time` after execution.
        """
        time_step = TimeDuration(time_step).seconds
        self.__default_simulation_settings = {
            self._RESTART: restart,
            self._TIME_STEP: time_step,
        }
        self.__simulation_settings = {}
        self.__do_step = do_step
        self.__set_time_manager(initial_time, final_time, time_step)
        self._time = None

    def __set_time_manager(
        self,
        initial_time: TimeDurationType | None,
        final_time: TimeDurationType | None,
        time_step: TimeDurationType,
    ) -> None:
        """Set the time_manager.

        Args:
            initial_time: The initial time of the simulation;
                if `None`, use the start time defined in the FMU model if any;
                otherwise use 0.
            final_time: The final time of the simulation;
                if `None`, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
            time_step: The time step of the simulation.
                If `0.`, it is computed by the wrapped library `fmpy`.
        """
        if time_step == 0.0:
            time_step = self.__get_field_value(
                self.__model_description.defaultExperiment, "stepSize", 0.0
            )
            if time_step == 0.0 and self._WARN_ABOUT_ZERO_TIME_STEP:
                LOGGER.warning(
                    "The time step of the FMUDiscipline %r is equal to 0.", self.name
                )
            self.__default_simulation_settings[self._TIME_STEP] = time_step
        else:
            time_step = TimeDuration(time_step).seconds

        if initial_time is None:
            initial_time = self.__get_field_value(
                self.__model_description.defaultExperiment, "startTime", 0.0
            )
        else:
            initial_time = TimeDuration(initial_time).seconds

        self.__time_manager = TimeManager(initial_time, final_time, time_step)
        self.__set_final_time(final_time)
        self._initial_values[self._TIME] = array([initial_time])

    def __set_final_time(self, final_time: TimeDurationType) -> None:
        """Set the final time.

        Args:
            final_time: The final time of the simulation;
                if `None`, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
        """
        if final_time is None:
            self.__time_manager.final = self.__get_field_value(
                self.__model_description.defaultExperiment,
                "stopTime",
                self.__time_manager.initial,
            )
        else:
            self.__time_manager.final = TimeDuration(final_time).seconds

        if self.__do_step:
            self.__default_simulation_settings[self._SIMULATION_TIME] = 0.0
        else:
            self.__default_simulation_settings[self._SIMULATION_TIME] = (
                self.__time_manager.remaining
            )

    def __set_fmu_model(
        self,
        file_path: str | Path,
        model_instance_directory: str | Path,
        do_step: bool,
        use_co_simulation: bool,
        name: str,
    ) -> str:
        """Read the FMU model.

        Args:
            file_path: The path to the FMU model file.
            model_instance_directory: The directory of the FMU instance,
                containing the files extracted from the FMU model file;
                if empty, let `fmpy` create a temporary directory.
            do_step: Whether the model is simulated over only one `time_step`
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            use_co_simulation: Whether the co-simulation FMI type is used.
                Otherwise, use model-exchange FMI type.
                When `do_step` is `True`, the co-simulation FMI type is required.
            name: The default name of the discipline.
                If empty, deduce it from the FMU file.

        Returns:
            The name of the discipline.
        """
        # The path to the FMU file, which is a ZIP archive.
        self.__file_path = Path(file_path)

        # The path to unzipped archive.
        self.__model_dir_path = Path(
            extract(str(file_path), unzipdir=model_instance_directory or None)
        ).resolve()

        # The description of the FMU model, read from the XML file in the archive.
        self.__model_description = read_model_description(str(self.__model_dir_path))
        self.__model_name = self.__model_description.modelName
        self.__model_fmi_version = self.__model_description.fmiVersion
        self.__use_fmi_3 = self.__model_fmi_version == "3.0"
        self.__model_type = (
            self._CO_SIMULATION if use_co_simulation else self._MODEL_EXCHANGE
        )
        name = name or self.__model_description.modelName or self.__class__.__name__
        if do_step and not use_co_simulation:
            LOGGER.warning(
                (
                    "The FMUDiscipline %r requires a co-simulation model "
                    "when do_step is True."
                ),
                name,
            )
            self.__model_type = self._CO_SIMULATION

        # Instantiation of the FMU model.
        self.__model = instantiate_fmu(
            self.__model_dir_path,
            self.__model_description,
            fmi_type=self.__model_type,
        )
        self.__parameter_setter_name = "setFloat64" if self.__use_fmi_3 else "setReal"
        self.__parameter_getter_name = "getFloat64" if self.__use_fmi_3 else "getReal"
        return name

    def __set_initial_values(self) -> None:
        """Set the initial values of the inputs and outputs of the disciplines."""
        self._initial_values = {}
        from_fmu_names = self.__from_fmu_names
        for variable in self.__model_description.modelVariables:
            variable_name = from_fmu_names.get(variable.name)
            if variable_name is not None:
                try:
                    initial_value = float(variable.start)
                except TypeError:
                    initial_value = None

                self._initial_values[variable_name] = array([initial_value])

    def __set_variable_names_references_and_causalities(
        self,
        input_names: Iterable[str] | None,
        output_names: Iterable[str],
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Set the names of the FMU variables and their causalities.

        Args:
            input_names: The names of the FMU model inputs;
                if empty, use all the inputs and parameters of the FMU model;
                if `None`, do not use inputs.
            output_names: The names of the FMU model outputs.
                if empty, use all the outputs of the FMU model.

        Returns:
            The names of the discipline inputs and outputs.

        Raises:
            ValueError: When a variable to rename is not an FMU variable.
        """
        # The names of all the input and output variables.
        all_input_names = []
        all_output_names = []

        # The causalities of the variables bound to the names of the variables.
        self.__causalities_to_variable_names = {}
        for variable in self.__model_description.modelVariables:
            causality = variable.causality
            variable_name = variable.name
            if causality in [self._Causality.INPUT, self._Causality.PARAMETER]:
                all_input_names.append(variable_name)
            elif causality == self._Causality.OUTPUT:
                all_output_names.append(variable_name)

            if causality not in self.__causalities_to_variable_names:
                self.__causalities_to_variable_names[causality] = []

            self.__causalities_to_variable_names[causality].append(variable_name)

        from_fmu_names = self.__from_fmu_names
        to_fmu_names = self.__to_fmu_names

        # The names of the input and output variables of the discipline.
        fmu_input_names = tuple(
            [] if input_names is None else input_names or all_input_names
        )
        self.__fmu_output_names = tuple(output_names or all_output_names)

        names = (
            set(from_fmu_names)
            - {self._TIME}
            - set(fmu_input_names)
            - set(self.__fmu_output_names)
        )
        if names:
            msg = f"{names} are not FMU variable names."
            raise ValueError(msg)

        for names in [fmu_input_names, self.__fmu_output_names]:
            for name in names:
                if name not in from_fmu_names:
                    to_fmu_names[name] = from_fmu_names[name] = name

        discipline_input_names = tuple(
            from_fmu_names[input_name] for input_name in fmu_input_names
        )
        discipline_output_names = tuple(
            from_fmu_names[output_name] for output_name in self.__fmu_output_names
        )

        # The reference values bound to the variable names.
        self.__names_to_references = {
            from_fmu_names[variable_name]: variable.valueReference
            for variable in self.__model_description.modelVariables
            if (variable_name := variable.name) in fmu_input_names
            or variable_name in self.__fmu_output_names
        }

        return discipline_input_names, discipline_output_names

    @staticmethod
    def __get_field_value(
        default_experiment: DefaultExperiment | None,
        field: str,
        default_value: float | None,
    ) -> float:
        """Get the value of a field of a default experiment.

        Args:
            default_experiment: The default experiment.
                If `None`, return `default_value`.
            field: The field of the experiment.
            default_value: The default value if `experiment` is `None`
                or if the field is missing or its value is `None`.

        Returns:
            The default value of the field.
        """
        if default_experiment is None:
            return default_value

        value = getattr(default_experiment, field)
        if value is None:
            return default_value

        return float(value)

    @property
    def model_description(self) -> ModelDescription:
        """The description of the FMU model."""
        return self.__model_description

    @property
    def model(self) -> FMUModel:
        """The FMU model."""
        return self.__model

    @property
    def causalities_to_variable_names(self) -> dict[str, list[str]]:
        """The names of the variables sorted by causality."""
        return self.__causalities_to_variable_names

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + "\n"
            + fmu_info(self.__file_path, [c.value for c in self._Causality])
        )

    def _pre_instantiate(self, **kwargs: Any) -> None:
        """Some actions to be done just before calling `BaseFMUDiscipline.__init__`.

        Args:
            **kwargs: The parameters of the method.
        """

    def execute(  # noqa:D102
        self,
        input_data: Mapping[
            str, ndarray | TimeSeries | Callable[[TimeDurationType], float]
        ] = MappingProxyType({}),
    ) -> DisciplineData:
        self.__executed = True
        full_input_data = self.io.prepare_input_data(input_data)
        self.__names_to_time_functions = {
            name: value.compute
            for name, value in full_input_data.items()
            if isinstance(value, TimeSeries)
        }
        self.__names_to_time_functions.update({
            name: value
            for name, value in full_input_data.items()
            if isinstance(value, Callable)
        })
        full_input_data.update({
            name: array([value.observable[0]])
            for name, value in full_input_data.items()
            if isinstance(value, TimeSeries)
        })
        full_input_data.update({
            name: array([value(self.__time_manager.current)])
            for name, value in full_input_data.items()
            if isinstance(value, Callable)
        })
        return super().execute(full_input_data)

    def set_default_execution(
        self,
        do_step: bool | None = None,
        final_time: TimeDurationType | None = None,
        restart: bool | None = None,
        time_step: TimeDurationType | None = None,
    ) -> None:
        """Change the default simulation settings.

        Args:
            do_step: Whether the model is simulated over only one `time_step`
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
                If `None`, use the value considered at the instantiation.
            final_time: The final time of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                If `None`, use the value considered at the instantiation.
            restart: Whether to restart the model at `initial_time`
                before executing it;
                if `None`, use the value passed at the instantiation.
            time_step: The time step of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                If `None`, use the value considered at the instantiation.
        """
        if do_step is not None:
            self.__do_step = do_step

        if restart is not None:
            self.__default_simulation_settings[self._RESTART] = restart

        if final_time is not None:
            self.__set_final_time(final_time)

        if time_step is not None:
            time_step = TimeDuration(time_step).seconds
            self.__default_simulation_settings[self._TIME_STEP] = time_step

    def set_next_execution(
        self,
        restart: bool | None = None,
        simulation_time: TimeDurationType | None = None,
        time_step: TimeDurationType | None = None,
    ) -> None:
        """Change the simulation settings for the execution.

        Args:
            restart: Whether to restart the model at `initial_time`
                before executing it;
                if `None`, use the value passed at the instantiation.
            simulation_time: The duration of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                if `None` and the `do_step` passed at instantiation is `False`,
                execute until the final time;
                if `None` and the `do_step` passed at instantiation is `True`,
                execute during a single time step.
            time_step: The time step of the simulation;
                either a number in seconds or a string of characters
                (see [TimeDuration][gemseo_fmu.utils.time_duration.TimeDuration]);
                if `None`, use the value passed at the instantiation.
        """  # noqa: D205 D212 D415
        if not self.__simulation_settings:
            self.__simulation_settings = copy(self.__default_simulation_settings)

        if time_step is not None:
            self.__simulation_settings[self._TIME_STEP] = TimeDuration(
                time_step
            ).seconds

        if restart is not None:
            self.__simulation_settings[self._RESTART] = restart

        if simulation_time is not None:
            simulation_time = TimeDuration(simulation_time).seconds
            self.__simulation_settings[self._SIMULATION_TIME] = simulation_time

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        if not self.__simulation_settings:
            self.__simulation_settings = self.__default_simulation_settings

        if self.__simulation_settings[self._RESTART]:
            self.__time_manager.reset()

        if self.__time_manager.is_initial:
            self.__model.reset()
            if self.__use_fmi_3:
                self.__model.enterInitializationMode(
                    tolerance=self.__get_field_value(
                        self.__model_description.defaultExperiment, "tolerance", None
                    ),
                    startTime=self.__time_manager.current,
                )
            else:
                self.__model.setupExperiment(
                    tolerance=self.__get_field_value(
                        self.__model_description.defaultExperiment, "tolerance", None
                    ),
                    startTime=self.__time_manager.current,
                )
                self.__model.enterInitializationMode()

            self.__model.exitInitializationMode()

        if not self.__time_manager.is_initial and self.__time_manager.is_final:
            msg = (
                f"The FMUDiscipline {self.name!r} cannot be executed "
                "as its current time is its final time "
                f"({self.__time_manager.current})."
            )
            raise ValueError(msg)

        input_data = self.get_input_data(with_namespaces=False)
        simulate = self.__run_one_step if self.__do_step else self.__run_to_final_time
        simulate(input_data)
        self.__simulation_settings = {}

    def __del__(self) -> None:
        if self.__executed:
            self.__model.terminate()
        self.__model.freeInstance()
        if self.__delete_model_instance_directory:
            rmtree(self.__model_dir_path, ignore_errors=True)

    def __run_one_step(self, input_data: Mapping[str, NumberArray]) -> None:
        """Simulate the FMU model during a single time step.

        Args:
            input_data: The values of the FMU model inputs.
        """
        time_step = self.__simulation_settings[self._TIME_STEP]
        if time_step == 0.0:
            # This is a static discipline.
            time_manager = self.__time_manager
            current_time = time_manager.current
            self.__set_model_inputs(input_data, current_time, True)
            self.__model.doStep(
                currentCommunicationPoint=current_time,
                communicationStepSize=time_step,
            )
        else:
            step = self.__simulation_settings[self._SIMULATION_TIME] or time_step
            time_manager = self.__time_manager.update_current_time(step)
            time_manager.step = time_step
            while True:
                try:
                    current_time = time_manager.current
                    time_step = time_manager.update_current_time().step
                except ValueError:
                    break

                self.__set_model_inputs(input_data, time_manager.current, True)
                self.__model.doStep(
                    currentCommunicationPoint=current_time,
                    communicationStepSize=time_step,
                )

        self._time = array([time_manager.final])
        output_data = {}
        getter = getattr(self.__model, self.__parameter_getter_name)
        for output_name in self.io.output_grammar.names_without_namespace:
            if output_name == self._TIME:
                output_data[self._TIME] = self._time
            else:
                output_data[output_name] = array(
                    getter([self.__names_to_references[output_name]])
                )
        self.io.update_output_data(output_data)

    def __set_model_inputs(
        self, input_data: Mapping[str, NumberArray], time: float, store: bool
    ) -> None:
        """Set the FMU model inputs.

        Args:
            input_data: The input values.
            time: The evaluation time.
        """
        for input_name, input_value in input_data.items():
            if input_name in self.__names_to_time_functions:
                try:
                    value = self.__names_to_time_functions[input_name](time)
                except ValueError:
                    continue

                if store:
                    self.io.data[input_name] = array([value])
            elif isinstance(input_value, ndarray):
                value = input_value[0]
            else:
                value = input_value

            getattr(self.__model, self.__parameter_setter_name)(
                [self.__names_to_references[input_name]], [value]
            )

    def __do_when_step_finished(self, time: float, recorder: Recorder) -> bool:
        """Callback to interact with the simulation after each time step.

        Try to change the values of the parameters passed as TimeSeries.

        Args:
            time: The current time.
            recorder: A helper to record the variables during the simulation.
        """
        fmu = recorder.fmu
        for name, function in self.__names_to_time_functions.items():
            try:
                value = function(time)
            except ValueError:
                continue

            getattr(fmu, self.__parameter_setter_name)(
                [self.__names_to_references[name]], [value]
            )
            self.io.data[name] = append(self.io.data[name], value)

        return True

    def __run_to_final_time(self, input_data: Mapping[str, NumberArray]) -> None:
        """Simulate the FMU model from the current time to the final time.

        Args:
            input_data: The values of the FMU model inputs.
        """
        simulation_time = self.__simulation_settings[self._SIMULATION_TIME]
        time_manager = self.__time_manager.update_current_time(simulation_time)
        time_step = self.__simulation_settings[self._TIME_STEP]
        self.__set_model_inputs(input_data, time_manager.initial, False)
        result = simulate_fmu(
            self.__model_dir_path,
            start_time=time_manager.initial,
            stop_time=time_manager.final,
            solver=self.__solver_name,
            output_interval=1
            if self.__time_manager.is_constant
            else (time_step or None),
            output=self.__fmu_output_names,
            fmu_instance=self.__model,
            model_description=self.__model_description,
            step_finished=self.__do_when_step_finished,
            initialize=False,
            terminate=False,
        )
        self._time = result[self._TIME]
        output_data = {
            name: array(result[self.__to_fmu_names[name]])
            for name in self.io.output_grammar.names_without_namespace
        }
        self.io.update_output_data(output_data)

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        super().__setstate__(state)
        self.__model = instantiate_fmu(
            self.__model_dir_path,
            self.__model_description,
            fmi_type=self.__model_type,
        )

    _ATTR_NOT_TO_SERIALIZE = Discipline._ATTR_NOT_TO_SERIALIZE.union([
        "_BaseFMUDiscipline__model"
    ])
