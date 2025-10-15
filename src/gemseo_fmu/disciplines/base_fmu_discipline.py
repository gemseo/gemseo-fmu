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
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Final

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
from strenum import StrEnum

from gemseo_fmu.disciplines._variables import FMU3Variable
from gemseo_fmu.disciplines._variables import FMUTimeVariable
from gemseo_fmu.disciplines._variables import RealVariable
from gemseo_fmu.utils.time_duration import TimeDuration
from gemseo_fmu.utils.time_manager import TimeManager
from gemseo_fmu.utils.time_series import TimeSeries

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from fmpy.model_description import DefaultExperiment
    from fmpy.model_description import ModelDescription
    from fmpy.simulation import Recorder
    from gemseo.core.discipline.discipline_data import DisciplineData
    from gemseo.typing import NumberArray
    from gemseo.typing import RealArray
    from gemseo.typing import StrKeyMapping
    from numpy import ndarray

    from gemseo_fmu.disciplines._variables import BaseFMUVariable
    from gemseo_fmu.utils.time_duration import TimeDurationType

FMUModel = FMU1Model | FMU2Model | FMU3Model | FMU1Slave | FMU2Slave | FMU3Slave

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

    _DO_STEP: Final[str] = "do_step"

    @dataclass
    class _SimulationSettings:
        """The simulation settings."""

        initialize_only: bool
        """Whether the model simply needs to be initialized (no time integration)."""

        restart: bool
        """Whether the model is restarted at initial time after execution."""

        simulation_time: float
        """The simulation time of the next execution."""

        time_step: float
        """The simulation time step."""

        use_arrays_only: bool
        """Whether to use array data only."""

    _WARN_ABOUT_ZERO_TIME_STEP: ClassVar[bool] = True
    """Whether to log a warning message when the time step is zero."""

    __causalities_to_variable_names: dict[str, list[str]]
    """The names of the variables sorted by causality."""

    __default_simulation_settings: _SimulationSettings
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

    __fmu_input_names: tuple[str]
    """The names of the FMU model inputs and parameters used by the discipline."""

    __fmu_output_names: tuple[str]
    """The names of the FMU model outputs used by the discipline."""

    __from_fmu_names: dict[str, str]
    """The map from the FMU variable names to the discipline variable names."""

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

    __simulation_settings: _SimulationSettings | None
    """The simulation settings for the next execution, if defined."""

    __solver_name: str
    """The name of the ODE solver."""

    __time: RealArray | None
    """The time steps of the last execution; `None` when not yet executed."""

    __functional_input_names: list[str]
    """The name of the input variables whose values are functions."""

    __time_variable: FMUTimeVariable
    """The time variable."""

    __time_manager: TimeManager
    """The time manager."""

    __use_fmi_3: bool
    """Whether the FMU model is based on FMI 3.0."""

    __validate: bool
    """Whether the FMU model must be checked."""

    _to_fmu_variables: dict[str, BaseFMUVariable | FMUTimeVariable]
    """The mapping between variable names and FMU variables."""

    __BOOLEAN_WORDS_TO_VALUES: Final[dict[str, bool]] = {"false": False, "true": True}
    """The mapping between words for boolean values and boolean values."""

    def __init__(
        self,
        file_path: str | Path,
        input_names: Iterable[str] | None = (),
        output_names: Iterable[str] = (),
        initial_time: TimeDurationType | None = None,
        final_time: TimeDurationType | None = None,
        time_step: TimeDurationType = 0.0,
        time_name: str = "time",
        add_time_to_output_grammar: bool = True,
        restart: bool = True,
        do_step: bool = False,
        name: str = "",
        use_co_simulation: bool = True,
        solver_name: Solver = Solver.CVODE,
        model_instance_directory: str | Path = "",
        delete_model_instance_directory: bool = True,
        variable_names: Mapping[str, str] = READ_ONLY_EMPTY_DICT,
        validate: bool = True,
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
            time_name: The name of the time variable in the FMU model.
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
            validate: Whether the FMU file must be checked.
            **pre_instantiation_parameters: The parameters to be passed
                to `_pre_instantiate()`.
        """  # noqa: D205 D212 D415
        self.__delete_model_instance_directory = delete_model_instance_directory
        self.__executed = False
        self.__solver_name = str(solver_name)
        self.name = self.__set_fmu_model(
            file_path,
            validate,
            model_instance_directory,
            do_step,
            use_co_simulation,
            name,
        )
        self.__from_fmu_names = dict(variable_names)
        disciplinary_time_name = f"{self.name}_{time_name}"
        self.__time_variable = FMUTimeVariable(time_name, disciplinary_time_name)
        self.__from_fmu_names[time_name] = disciplinary_time_name
        self.__functional_input_names = []
        input_names, output_names = (
            self.__set_variable_names_references_and_causalities(
                input_names, output_names
            )
        )
        initial_time = self.__set_time(
            initial_time, final_time, time_step, do_step, restart
        )
        self._pre_instantiate(**(pre_instantiation_parameters or {}))
        super().__init__(name=self.name)

        self.io.input_grammar.update_from_types(
            dict.fromkeys(
                input_names, bool | int | float | str | NDArrayPydantic | TimeSeries
            )
        )
        self.io.output_grammar.update_from_names(output_names)
        self.__define_fmu_variables()
        self.__set_initial_values()
        self.__time_variable.initial = array([initial_time])
        if add_time_to_output_grammar:
            self.io.output_grammar.update_from_types({
                disciplinary_time_name: float | NDArrayPydantic[float]
            })
            self._to_fmu_variables[disciplinary_time_name] = self.__time_variable

        self.io.input_grammar.defaults = {
            input_name: self._to_fmu_variables[input_name].initial
            for input_name in input_names
        }

    def __set_time(
        self,
        initial_time: TimeDurationType | None,
        final_time: TimeDurationType | None,
        time_step: TimeDurationType,
        do_step: bool,
        restart: bool,
    ) -> float:
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

        Returns:
            The initial time.
        """
        time_step = TimeDuration(time_step).seconds
        self.__default_simulation_settings = self._SimulationSettings(
            restart=restart,
            time_step=time_step,
            initialize_only=False,
            use_arrays_only=False,
            simulation_time=0.0,
        )
        self.__simulation_settings = None
        self.__do_step = do_step
        initial_time = self.__set_time_manager(initial_time, final_time, time_step)
        self._time = None
        return initial_time

    def __set_time_manager(
        self,
        initial_time: TimeDurationType | None,
        final_time: TimeDurationType | None,
        time_step: TimeDurationType,
    ) -> float:
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

        Returns:
            The initial time.
        """
        if time_step == 0.0:
            time_step = self.__get_field_value(
                self.__model_description.defaultExperiment, "stepSize", 0.0
            )
            if time_step == 0.0 and self._WARN_ABOUT_ZERO_TIME_STEP:
                LOGGER.warning(
                    "The time step of the FMUDiscipline %r is equal to 0.", self.name
                )
            self.__default_simulation_settings.time_step = time_step
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

        return initial_time

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
            self.__default_simulation_settings.simulation_time = 0.0
        else:
            self.__default_simulation_settings.simulation_time = (
                self.__time_manager.remaining
            )

    def __set_fmu_model(
        self,
        file_path: str | Path,
        validate: bool,
        model_instance_directory: str | Path,
        do_step: bool,
        use_co_simulation: bool,
        name: str,
    ) -> str:
        """Read the FMU model.

        Args:
            file_path: The path to the FMU model file.
            validate: Whether the FMU model file must be checked.
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

        self.__validate = validate

        # The path to unzipped archive.
        self.__model_dir_path = Path(
            extract(str(file_path), unzipdir=model_instance_directory or None)
        ).resolve()

        # The description of the FMU model, read from the XML file in the archive.
        self.__model_description = read_model_description(
            str(self.__model_dir_path), validate=validate
        )
        self.__model_name = self.__model_description.modelName
        self.__model_fmi_version = self.__model_description.fmiVersion
        self.__use_fmi_3 = self.__model_fmi_version == "3.0"
        self.__model_type = "CoSimulation" if use_co_simulation else "ModelExchange"
        name = name or self.__model_description.modelName or self.__class__.__name__
        if do_step and not use_co_simulation:
            LOGGER.warning(
                (
                    "The FMUDiscipline %r requires a co-simulation model "
                    "when do_step is True."
                ),
                name,
            )
            self.__model_type = "CoSimulation"

        # Instantiation of the FMU model.
        self.__instantiate_fmu_model()
        return name

    def __instantiate_fmu_model(self) -> None:
        """Instantiate the FMU model."""
        self.__model = instantiate_fmu(
            self.__model_dir_path,
            self.__model_description,
            fmi_type=self.__model_type,
            require_functions=self.__validate,
        )

    def __define_fmu_variables(self) -> None:
        """Define the mapping between variables names and FMU variables."""
        from_fmu_names = self.__from_fmu_names
        names_to_references = {
            from_fmu_names[variable_name]: variable.valueReference
            for variable in self.__model_description.modelVariables
            if (variable_name := variable.name) in self.__fmu_input_names
            or variable_name in self.__fmu_output_names
        }
        names_to_sizes = {}
        for variable in self.__model_description.modelVariables:
            variable_name = from_fmu_names.get(variable.name)
            if variable_name is not None:
                names_to_sizes[variable_name] = (
                    variable.dimensions[0].start if variable.dimensions else 1
                )
        if self.__use_fmi_3:
            fmu_names_to_types = {
                variable.name: (
                    variable.type if variable.type != "Enumeration" else "Int64"
                )
                for variable in self.__model_description.modelVariables
                if variable.name in self.__from_fmu_names
            }
            self._to_fmu_variables = {
                (disciplinary_name := self.__from_fmu_names[fmu_name]): FMU3Variable(
                    fmu_name,
                    disciplinary_name,
                    getattr(self.__model, f"get{fmu_names_to_types[fmu_name]}"),
                    getattr(self.__model, f"set{fmu_names_to_types[fmu_name]}"),
                    names_to_references[disciplinary_name],
                    names_to_sizes[disciplinary_name],
                )
                for fmu_names in (self.__fmu_input_names, self.__fmu_output_names)
                for fmu_name in fmu_names
            }
        else:
            self._to_fmu_variables = {
                (disciplinary_name := self.__from_fmu_names[fmu_name]): RealVariable(
                    fmu_name,
                    disciplinary_name,
                    self.__model.getReal,
                    self.__model.setReal,
                    names_to_references[disciplinary_name],
                )
                for fmu_names in (self.__fmu_input_names, self.__fmu_output_names)
                for fmu_name in fmu_names
            }

    def __set_initial_values(self) -> None:
        """Set the initial values of the inputs and outputs of the disciplines."""
        from_fmu_names = self.__from_fmu_names
        to_fmu_variables = self._to_fmu_variables
        func = self.__cast_string_value if self.__use_fmi_3 else float
        for variable in self.__model_description.modelVariables:
            fmu_variable_name = variable.name
            if (
                fmu_variable_name not in self.__fmu_input_names
                and fmu_variable_name not in self.__fmu_output_names
            ):
                continue

            variable_name = from_fmu_names.get(fmu_variable_name)
            if variable_name is not None:
                initial_value = variable.start
                if initial_value is not None:
                    initial_value = func(initial_value)

                to_fmu_variables[variable_name].initial = array([initial_value])

    @classmethod
    def __cast_string_value(cls, value: str) -> bool | int | float | str:
        """Cast a string value.

        Args:
            value: The string value.

        Returns:
            The final value.
        """
        if (boolean := cls.__BOOLEAN_WORDS_TO_VALUES.get(value)) is not None:
            return boolean

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            return value

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
        causalities_to_variable_names = self.__causalities_to_variable_names = {}
        for variable in self.__model_description.modelVariables:
            causality = variable.causality
            variable_name = variable.name
            if causality in {self._Causality.INPUT, self._Causality.PARAMETER}:
                all_input_names.append(variable_name)
            elif causality == self._Causality.OUTPUT:
                all_output_names.append(variable_name)

            if causality not in causalities_to_variable_names:
                causalities_to_variable_names[causality] = []

            causalities_to_variable_names[causality].append(variable_name)

        from_fmu_names = self.__from_fmu_names

        # The names of the input and output variables of the discipline.
        self.__fmu_input_names = tuple(
            [] if input_names is None else input_names or all_input_names
        )
        self.__fmu_output_names = tuple(output_names or all_output_names)

        names = (
            set(from_fmu_names)
            - {self.__time_variable.name}
            - set(self.__fmu_input_names)
            - set(self.__fmu_output_names)
        )
        if names:
            msg = f"{names} are not FMU variable names."
            raise ValueError(msg)

        for names in [self.__fmu_input_names, self.__fmu_output_names]:
            for name in set(names).difference(from_fmu_names):
                from_fmu_names[name] = name

        discipline_input_names = tuple(
            from_fmu_names[input_name] for input_name in self.__fmu_input_names
        )
        discipline_output_names = tuple(
            from_fmu_names[output_name] for output_name in self.__fmu_output_names
        )
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
        if self.__default_simulation_settings.use_arrays_only:
            return super().execute(input_data)

        full_input_data = self.io.prepare_input_data(input_data)
        current_time = self.__time_manager.current
        self.__functional_input_names = []
        for name, value in full_input_data.items():
            cls = value.__class__
            if issubclass(cls, TimeSeries):
                self._to_fmu_variables[name].time_function = value.compute
                full_input_data[name] = array([value.observable[0]])
                self.__functional_input_names.append(name)
            elif issubclass(cls, Callable):
                self._to_fmu_variables[name].time_function = value
                full_input_data[name] = array([value(current_time)])
                self.__functional_input_names.append(name)

        return super().execute(full_input_data)

    def set_default_execution(
        self,
        do_step: bool | None = None,
        final_time: TimeDurationType | None = None,
        restart: bool | None = None,
        time_step: TimeDurationType | None = None,
        initialize_only: bool = False,
        use_arrays_only: bool = False,
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
            initialize_only: Whether the model simply needs to be initialized
                (no time integration).
            use_arrays_only: Whether to use array data only.
        """
        if do_step is not None:
            self.__do_step = do_step

        if restart is not None:
            self.__default_simulation_settings.restart = restart

        if final_time is not None:
            self.__set_final_time(final_time)

        if time_step is not None:
            time_step = TimeDuration(time_step).seconds
            self.__default_simulation_settings.time_step = time_step

        self.__default_simulation_settings.initialize_only = initialize_only
        self.__default_simulation_settings.use_arrays_only = use_arrays_only

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
        if self.__simulation_settings is None:
            self.__simulation_settings = copy(self.__default_simulation_settings)

        if time_step is not None:
            self.__simulation_settings.time_step = TimeDuration(time_step).seconds

        if restart is not None:
            self.__simulation_settings.restart = restart

        if simulation_time is not None:
            simulation_time = TimeDuration(simulation_time).seconds
            self.__simulation_settings.simulation_time = simulation_time

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping:
        if self.__simulation_settings is None:
            self.__simulation_settings = self.__default_simulation_settings

        time_manager = self.__time_manager
        if self.__simulation_settings.restart:
            time_manager.reset()

        if time_manager.is_initial:
            self.__model.reset()
            self.__set_model_inputs(input_data, time_manager.current, True)
            if self.__use_fmi_3:
                self.__model.enterInitializationMode(
                    tolerance=self.__get_field_value(
                        self.__model_description.defaultExperiment, "tolerance", None
                    ),
                    startTime=time_manager.current,
                )
            else:
                self.__model.setupExperiment(
                    tolerance=self.__get_field_value(
                        self.__model_description.defaultExperiment, "tolerance", None
                    ),
                    startTime=time_manager.current,
                )
                self.__model.enterInitializationMode()

            self.__model.exitInitializationMode()
            if self.__default_simulation_settings.initialize_only:
                time_name = self.__time_variable.disciplinary_name
                return {
                    output_name: (
                        array([0.0])
                        if output_name == time_name
                        else array(self._to_fmu_variables[output_name].get_value())
                    )
                    for output_name in self.io.output_grammar.names_without_namespace
                }

        if not time_manager.is_initial and time_manager.is_final:
            msg = (
                f"The FMUDiscipline {self.name!r} cannot be executed "
                "as its current time is its final time "
                f"({self.__time_manager.current})."
            )
            raise ValueError(msg)

        simulate = self.__run_one_step if self.__do_step else self.__run_to_final_time
        output_data = simulate(input_data)
        self.__simulation_settings = None
        return output_data

    def __del__(self) -> None:
        if self.__executed:
            self.__model.terminate()
        self.__model.freeInstance()
        if self.__delete_model_instance_directory:
            rmtree(self.__model_dir_path, ignore_errors=True)

    def __run_one_step(
        self, input_data: Mapping[str, NumberArray]
    ) -> dict[str, NumberArray]:
        """Simulate the FMU model during a single time step.

        Args:
            input_data: The values of the FMU model inputs.

        Returns:
            The output data.
        """
        time_step = self.__simulation_settings.time_step
        if time_step == 0.0:
            # This is a static discipline.
            time_manager = self.__time_manager
            final_time = start_time = time_manager.current
            self.__set_model_inputs(input_data, start_time, True)
            self.__model.doStep(
                currentCommunicationPoint=start_time,
                communicationStepSize=time_step,
            )
        else:
            simulation_time = self.__simulation_settings.simulation_time
            if not simulation_time:
                simulation_time = time_step

            time_manager = self.__time_manager.update_current_time(step=simulation_time)
            run_model = self.__model.doStep
            set_model_inputs = self.__set_model_inputs
            update_current_time = time_manager.update_current_time
            start_time = time_manager.initial
            final_time = time_manager.final
            while start_time < final_time:
                _, intermediate_time, time_step = update_current_time(
                    step=time_step, return_time_manager=False
                )
                # TODO: why intermediate_time rather than start_time?
                set_model_inputs(input_data, intermediate_time, True)
                run_model(
                    currentCommunicationPoint=start_time,
                    communicationStepSize=time_step,
                )
                start_time = intermediate_time

        time = self._time = array([final_time])
        time_name = self.__time_variable.disciplinary_name
        output_data = {}
        for output_name in self.io.output_grammar.names_without_namespace:
            if output_name == time_name:
                output_value = time
            else:
                output_value = array(self._to_fmu_variables[output_name].get_value())

            output_data[output_name] = output_value

        return output_data

    def __set_model_inputs(
        self, input_data: Mapping[str, NumberArray], time: float, store: bool
    ) -> None:
        """Set the FMU model inputs.

        Args:
            input_data: The input values.
            time: The evaluation time.
        """
        data = self.io.data
        to_fmu_variables = self._to_fmu_variables
        for input_name, input_value in input_data.items():
            if (function := to_fmu_variables[input_name].time_function) is not None:
                try:
                    input_value = array([function(time)])
                except ValueError:
                    continue

                if store:
                    data[input_name] = input_value

            to_fmu_variables[input_name].set_value(input_value)

    def __do_when_step_finished(self, time: float, recorder: Recorder) -> bool:
        """Callback to interact with the simulation after each time step.

        Try to change the values of the parameters passed as TimeSeries.

        Args:
            time: The current time.
            recorder: A helper to record the variables during the simulation.
        """
        data = self.io.data
        for name in self.__functional_input_names:
            try:
                value = (variable := self._to_fmu_variables[name]).time_function(time)
            except ValueError:
                continue

            variable.set_value(value)
            data[name] = append(data[name], value)

        return True

    def __run_to_final_time(
        self, input_data: Mapping[str, NumberArray]
    ) -> dict[str, NumberArray]:
        """Simulate the FMU model from the current time to the final time.

        Args:
            input_data: The values of the FMU model inputs.

        Returns:
            The output data.
        """
        simulation_time = self.__simulation_settings.simulation_time
        time_step = self.__simulation_settings.time_step
        time_manager = self.__time_manager
        start_time = time_manager.current
        time_manager.update_current_time(simulation_time, return_time_manager=False)
        stop_time = time_manager.current
        self.__set_model_inputs(input_data, start_time, False)
        result = simulate_fmu(
            self.__model_dir_path,
            validate=self.__validate,
            start_time=start_time,
            stop_time=stop_time,
            solver=self.__solver_name,
            output_interval=1 if time_manager.is_constant else (time_step or None),
            output=self.__fmu_output_names,
            fmu_instance=self.__model,
            model_description=self.__model_description,
            step_finished=self.__do_when_step_finished,
            initialize=False,
            terminate=False,
        )
        self._time = result[self.__time_variable.name]
        return {
            name: array(result[self._to_fmu_variables[name].name])
            for name in self.io.output_grammar.names_without_namespace
        }

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        super().__setstate__(state)
        self.__instantiate_fmu_model()
        self.__define_fmu_variables()
        if self.__time_variable.disciplinary_name in self.io.output_grammar:
            self._to_fmu_variables[self.__time_variable.disciplinary_name] = (
                self.__time_variable
            )

    _ATTR_NOT_TO_SERIALIZE = Discipline._ATTR_NOT_TO_SERIALIZE.union([
        "_BaseFMUDiscipline__model",
        "_to_fmu_variables",
    ])
