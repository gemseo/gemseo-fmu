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
from pathlib import Path
from shutil import rmtree
from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Any
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
from gemseo.core.discipline import MDODiscipline
from numpy import array
from numpy import double
from numpy import interp
from numpy import ndarray
from numpy import vstack
from strenum import StrEnum

from gemseo_fmu.disciplines.time_series import TimeSeries

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping

    from fmpy.model_description import DefaultExperiment
    from fmpy.model_description import ModelDescription
    from fmpy.simulation import Recorder
    from numpy.typing import NDArray

FMUModel = Union[FMU1Model, FMU2Model, FMU3Model, FMU1Slave, FMU2Slave, FMU3Slave]

LOGGER = logging.getLogger(__name__)


class BaseFMUDiscipline(MDODiscipline):
    """A base discipline wrapping a Functional Mockup Unit (FMU) model.

    This discipline relies on [FMPy](https://github.com/CATIA-Systems/FMPy).
    """

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
    _FINAL_TIME: Final[str] = "final_time"
    _INITIAL_TIME: Final[str] = "initial_time"
    _MODEL_EXCHANGE: Final[str] = "ModelExchange"
    _RESTART: Final[str] = "restart"
    _SIMULATION_TIME: Final[str] = "simulation_time"
    _TIME: Final[str] = "time"
    _TIME_STEP: Final[str] = "time_step"
    _INPUT: Final[str] = _Causality.INPUT
    _PARAMETER: Final[str] = _Causality.PARAMETER
    _DO_STEP: Final[str] = "do_step"

    __file_path: Path
    """The path to the FMU file, which is a ZIP archive."""

    __delete_model_instance_directory: bool
    """Whether trying to delete the directory of the FMU instance when deleting the
    discipline."""

    __model_dir_path: Path
    """The description of the FMU model, read from the XML file in the archive."""

    __model_description: ModelDescription
    """The description of the FMU model."""

    __causalities_to_variable_names: dict[str, list[str]]
    """The names of the variables sorted by causality."""

    __model_name: str
    """The name of the FMU model."""

    __model_fmi_version: str
    """The FMI version of the FMU model."""

    __model: FMUModel
    """The FMU model."""

    __names_to_references: dict[str, int]
    """The value references bound to the variables names."""

    __current_time: float
    """The current time."""

    __time_step: float
    """The execution time step."""

    __do_step: bool
    """Whether the discipline is executed step by step."""

    __solver_name: str
    """The name of the ODE solver."""

    __default_simulation_settings: dict[str, bool | float]
    """The default values of the simulation settings."""

    __simulation_settings: dict[str, bool | float]
    """The values of the simulation settings."""

    __use_time_in_output_grammar: bool
    """Whether the time belongs to the output grammar."""

    __time: NDArray[float] | None
    """The time steps of the last execution; ``None`` when not yet executed."""

    __names_to_time_series: dict[str, TimeSeries]
    """The input names bound to the time series at the last execution."""

    __inputs_as_time_series: list[str]
    """The FMU inputs passed as ``TimeSeries`` at the last execution."""

    __parameters_as_time_series: list[str]
    """The FMU parameters passed as ``TimeSeries`` at the last execution."""

    __time_series_time_steps: NDArray[float]
    """The time steps of the time series after pre-processing of the original ones."""

    __fmpy_input_time_series: NDArray[float] | None
    """The fmpy-formatted input time series."""

    __input_input_names: list[str]
    """The discipline variables with input causality."""

    __input_names: list[str]
    """The discipline inputs."""

    __output_names: list[str]
    """The discipline outputs."""

    __parameter_input_names: list[str]
    """The discipline inputs with parameter causality."""

    _initial_values: dict[str, NDArray[float]]
    """The initial values of the discipline outputs."""

    _initial_time: float
    """The initial time."""

    _final_time: float
    """The final time."""

    __executed: bool
    """Whether the discipline has already been executed."""

    def __init__(
        self,
        file_path: str | Path,
        input_names: Iterable[str] | None = (),
        output_names: Iterable[str] = (),
        initial_time: float | None = None,
        final_time: float | None = None,
        time_step: float = 0.0,
        add_time_to_output_grammar: bool = True,
        restart: bool = True,
        do_step: bool = False,
        name: str = "",
        use_co_simulation: bool = True,
        solver_name: Solver = Solver.CVODE,
        model_instance_directory: str | Path = "",
        delete_model_instance_directory: bool = True,
        **pre_instantiation_parameters: Any,
    ) -> None:
        """
        Args:
            file_path: The path to the FMU model file.
            input_names: The names of the FMU model inputs;
                if empty, use all the inputs and parameters of the FMU model;
                if ``None``, do not use inputs.
            output_names: The names of the FMU model outputs.
                if empty, use all the outputs of the FMU model.
            initial_time: The initial time of the simulation;
                if ``None``, use the start time defined in the FMU model if any;
                otherwise use 0.
            final_time: The final time of the simulation;
                if ``None``, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
            time_step: The time step of the simulation.
                If ``0.``, it is computed by the wrapped library ``fmpy``.
            add_time_to_output_grammar: Whether the time is added to the output grammar.
            restart: Whether the model is restarted at ``initial_time`` after execution.
            do_step: Whether the model is simulated over only one ``time_step``
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            use_co_simulation: Whether the co-simulation FMI type is used.
                Otherwise, use model-exchange FMI type.
                When ``do_step`` is ``True``, the co-simulation FMI type is required.
            solver_name: The name of the solver to simulate a model-exchange model.
            model_instance_directory: The directory of the FMU instance,
                containing the files extracted from the FMU model file;
                if empty, let ``fmpy`` create a temporary directory.
            delete_model_instance_directory: Whether to delete the directory
                of the FMU instance when deleting the discipline.
            **pre_instantiation_parameters: The parameters to be passed
                to ``_pre_instantiate()``.
        """  # noqa: D205 D212 D415
        self.__delete_model_instance_directory = delete_model_instance_directory
        self.__executed = False
        self.__fmpy_input_time_series = None
        self.__names_to_time_series = {}
        self.__solver_name = str(solver_name)
        self.__set_fmu_model(
            file_path, model_instance_directory, do_step, use_co_simulation
        )
        self.__set_variable_names_references_and_causalities(input_names, output_names)
        inputs = self.__input_names
        outputs = self.__output_names
        self.__set_initial_values(inputs, outputs)
        self.__set_time(initial_time, final_time, time_step, do_step, restart)
        pre_instantiation_parameters = pre_instantiation_parameters or {}
        self._pre_instantiate(**pre_instantiation_parameters)
        super().__init__(
            name=(
                name or self.__model_description.modelName or self.__class__.__name__
            ),
            cache_type=self.CacheType.NONE,
        )
        self.__set_grammars(add_time_to_output_grammar, inputs, outputs)
        self.default_inputs = {
            input_name: self._initial_values[input_name] for input_name in inputs
        }

    def __set_grammars(
        self,
        add_time_to_output_grammar: bool,
        inputs: Iterable[str],
        outputs: Iterable[str],
    ) -> None:
        """Set the grammars of the inputs and outputs.

        Args:
            add_time_to_output_grammar: Whether the time is added to the output grammar.
            inputs: The names of the inputs.
            outputs: The names of the outputs.
        """
        self.input_grammar.update_from_names(inputs)
        self.output_grammar.update_from_names(outputs)
        self.__use_time_in_output_grammar = add_time_to_output_grammar
        if add_time_to_output_grammar:
            self.output_grammar.update_from_names([self._TIME])
            self.output_grammar.add_namespace(self._TIME, self.name)

    def __set_time(
        self,
        initial_time: float | None,
        final_time: float | None,
        time_step: float,
        do_step: bool,
        restart: bool,
    ) -> None:
        """Set all about time.

        Args:
            initial_time: The initial time of the simulation;
                if ``None``, use the start time defined in the FMU model if any;
                otherwise use 0.
            final_time: The final time of the simulation;
                if ``None``, use the stop time defined in the FMU model if any;
                otherwise use the initial time.
            time_step: The time step of the simulation.
                If ``0.``, it is computed by the wrapped library ``fmpy``.
            do_step: Whether the model is simulated over only one ``time_step``
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            restart: Whether the model is restarted at ``initial_time`` after execution.
        """
        if initial_time is None:
            self._initial_time = self.__get_field_value(
                self.__model_description.defaultExperiment, "startTime", 0.0
            )
        else:
            self._initial_time = initial_time

        self._initial_values[self._TIME] = array([self._initial_time])
        self.__current_time = self._initial_time
        if final_time is None:
            self._final_time = self.__get_field_value(
                self.__model_description.defaultExperiment,
                "stopTime",
                self._initial_time,
            )
        else:
            self._final_time = final_time

        self.__time_step = time_step
        self.__do_step = do_step
        self._time = None

        self.__simulation_settings = {}
        self.__default_simulation_settings = {
            self._RESTART: restart,
            self._TIME_STEP: self.__time_step,
        }
        if not do_step:
            self.__default_simulation_settings[self._SIMULATION_TIME] = (
                self._final_time - self._initial_time
            )

    def __set_fmu_model(
        self,
        file_path: str | Path,
        model_instance_directory: str | Path,
        do_step: bool,
        use_co_simulation: bool,
    ) -> None:
        """Read the FMU model.

        Args:
            file_path: The path to the FMU model file.
            model_instance_directory: The directory of the FMU instance,
                containing the files extracted from the FMU model file;
                if empty, let ``fmpy`` create a temporary directory.
            do_step: Whether the model is simulated over only one ``time_step``
                when calling
                [execute()][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline.execute].
                Otherwise, simulate the model from current time to final time in one go.
            use_co_simulation: Whether the co-simulation FMI type is used.
                Otherwise, use model-exchange FMI type.
                When ``do_step`` is ``True``, the co-simulation FMI type is required.
        """
        # The path to the FMU file, which is a ZIP archive.
        self.__file_path = Path(file_path)

        # The path to unzipped archive.
        self.__model_dir_path = Path(
            extract(str(file_path), unzipdir=model_instance_directory or None)
        ).resolve()

        # The description of the FMU model, read from the XML file in the archive.
        self.__model_description = read_model_description(self.__model_dir_path)
        self.__model_name = self.__model_description.modelName
        self.__model_fmi_version = self.__model_description.fmiVersion
        self.__model_type = (
            self._CO_SIMULATION if use_co_simulation else self._MODEL_EXCHANGE
        )
        if do_step and not use_co_simulation:
            LOGGER.warning(
                "The FMUDiscipline requires a co-simulation model when do_step is True."
            )
            self.__model_type = self._CO_SIMULATION

        # Instantiation of the FMU model.
        self.__model = instantiate_fmu(
            self.__model_dir_path,
            self.__model_description,
            fmi_type=self.__model_type,
        )

    def __set_initial_values(
        self, input_names: Iterable[str], output_names: Iterable[str]
    ) -> None:
        """Set the initial values of the inputs and outputs of the disciplines.

        Args:
            input_names: The names of the inputs of the discipline.
            output_names: The names of the outputs of the discipline.
        """
        self._initial_values = {}
        io_names = set(input_names).union(output_names)
        for variable in self.__model_description.modelVariables:
            variable_name = variable.name
            if variable_name in io_names:
                try:
                    initial_value = float(variable.start)
                except TypeError:
                    initial_value = None

                self._initial_values[variable_name] = array([initial_value])

    def __set_variable_names_references_and_causalities(
        self, input_names: Iterable[str] | None = (), output_names: Iterable[str] = ()
    ) -> None:
        """Set the names of the FMU variables and their causalities.

        Args:
            input_names: The names of the FMU model inputs;
                if empty, use all the inputs and parameters of the FMU model;
                if ``None``, do not use inputs.
            output_names: The names of the FMU model outputs.
                if empty, use all the outputs of the FMU model.
        """
        # The names of all the input and output variables.
        all_input_names = []
        all_output_names = []

        # The names of all the inputs and parameters of the FMU model.
        self.__input_input_names = []
        self.__parameter_input_names = []

        # The causalities of the variables bound to the names of the variables.
        self.__causalities_to_variable_names = {}
        for variable in self.__model_description.modelVariables:
            causality = variable.causality
            variable_name = variable.name
            if causality == self._Causality.INPUT:
                all_input_names.append(variable_name)
                self.__input_input_names.append(variable_name)
            elif causality == self._Causality.PARAMETER:
                all_input_names.append(variable_name)
                self.__parameter_input_names.append(variable_name)
            elif causality == self._Causality.OUTPUT:
                all_output_names.append(variable_name)

            if causality not in self.__causalities_to_variable_names:
                self.__causalities_to_variable_names[causality] = []

            self.__causalities_to_variable_names[causality].append(variable_name)

        # The names of the input and output variables of the discipline.
        outputs = output_names or all_output_names
        inputs = [] if input_names is None else input_names or all_input_names
        self.__input_names = inputs

        # The names of the FMU parameters and inputs.
        self.__parameter_input_names = [
            name for name in self.__parameter_input_names if name in inputs
        ]
        self.__input_input_names = [
            name for name in self.__input_input_names if name in inputs
        ]

        # The reference values bound to the variable names.
        self.__names_to_references = {
            variable.name: variable.valueReference
            for variable in self.__model_description.modelVariables
        }

        # The names of the FMU model outputs of interest.
        self.__output_names = outputs

    @staticmethod
    def __get_field_value(
        default_experiment: DefaultExperiment | None, field: str, default_value: float
    ) -> float:
        """Get the value of a field of a default experiment.

        Args:
            default_experiment: The default experiment.
                If ``None``, return ``default_value``.
            field: The field of the experiment.
            default_value: The default value if ``experiment`` is ``None``
                or if the field is missing or its value is ``None``.

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

    @property
    def _current_time(self) -> float:
        return self.__current_time

    @_current_time.setter
    def _current_time(self, current_time: float) -> None:
        """Set the current time.

        Args:
            current_time: The current time.

        Raises:
            ValueError: When the current time is greater than the final time.
        """
        if current_time > self._final_time:
            raise ValueError(
                f"The current time ({current_time}) is greater "
                f"than the final time ({self._final_time})."
            )

        self.__current_time = current_time

    def _pre_instantiate(self, **kwargs: Any) -> None:
        """Do different things before initializing the FMU model."""

    def execute(  # noqa:D102
        self, input_data: Mapping[str, ndarray | TimeSeries] = MappingProxyType({})
    ) -> dict[str, ndarray]:
        self.__executed = True
        full_input_data = self._filter_inputs(input_data)
        self.__names_to_time_series = {
            name: value
            for name, value in full_input_data.items()
            if isinstance(value, TimeSeries)
        }
        get_ts_variables = self.__get_variables_set_with_time_series
        self.__inputs_as_time_series = get_ts_variables(self._INPUT)
        self.__parameters_as_time_series = get_ts_variables(self._PARAMETER)
        self.__time_series_time_steps = array([self._current_time])
        if self.__names_to_time_series:
            self.__time_series_time_steps = time = array(
                sorted(
                    set.union(*[
                        set(ts.time) for ts in self.__names_to_time_series.values()
                    ])
                )
            )
            for name, ts in self.__names_to_time_series.items():
                self.__names_to_time_series[name] = TimeSeries(
                    time, interp(time, ts.time, ts.observable)
                )

            values = vstack(
                [time]
                + [
                    self.__names_to_time_series[name].observable
                    for name in self.__inputs_as_time_series
                ]
            )
            full_input_data.update({
                name: tuple(ts.observable)
                for name, ts in self.__names_to_time_series.items()
            })
            if len(values) > 1:
                self.__fmpy_input_time_series = array(
                    [tuple(row) for row in values.T],
                    dtype=[(self._TIME, double)]
                    + [(name, double) for name in self.__inputs_as_time_series],
                )
        return super().execute(full_input_data)

    def set_next_execution(
        self,
        restart: bool | None = None,
        simulation_time: float | None = None,
        time_step: float | None = None,
    ) -> None:
        """Change the simulation settings for the execution.

        Args:
            restart: Whether to restart the model at ``initial_time``
                before executing it;
                if ``None``, use the value passed at the instantiation.
            simulation_time: The duration of the simulation;
                if ``None``, execute until the final time.
            time_step: The time step of the simulation;
                if ``None``, use the value passed at the instantiation.
        """  # noqa: D205 D212 D415
        self.__simulation_settings = self.__default_simulation_settings.copy()
        if time_step is not None:
            self.__simulation_settings[self._TIME_STEP] = time_step

        if restart is not None:
            self.__simulation_settings[self._RESTART] = restart

        if simulation_time is not None:
            self.__simulation_settings[self._SIMULATION_TIME] = simulation_time

    def _run(self) -> None:
        if not self.__simulation_settings:
            self.__simulation_settings = self.__default_simulation_settings

        input_data = self.get_input_data(with_namespaces=False)
        if (
            self.__simulation_settings[self._RESTART]
            or self.__current_time == self._initial_time
        ):
            self.__current_time = self._initial_time
            self.__model.reset()
            self.__model.setupExperiment(startTime=self.__current_time)
            for parameter_name in self.__parameter_input_names:
                data = input_data[parameter_name]
                if not isinstance(data, TimeSeries):
                    self.__model.setReal(
                        [self.__names_to_references[parameter_name]], [data[0]]
                    )

            self.__model.enterInitializationMode()
            self.__model.exitInitializationMode()

        if self._initial_time < self.__current_time == self._final_time:
            raise ValueError(
                "The discipline cannot be executed "
                f"as the current time is the final time ({self.__current_time})."
            )

        if self.__do_step:
            self.__simulate_one_time_step(input_data)
        else:
            self.__simulate_to_final_time(input_data)

        self.__simulation_settings = {}

    def __del__(self) -> None:
        if self.__executed:
            self.__model.terminate()
        self.__model.freeInstance()
        if self.__delete_model_instance_directory:
            rmtree(self.__model_dir_path, ignore_errors=True)

    def __simulate_one_time_step(
        self, input_data: Mapping[str, NDArray[float]]
    ) -> None:
        """Simulate the FMU model during a single time step.

        Args:
            input_data: The values of the FMU model inputs.
        """
        time_step = self.__simulation_settings[self._TIME_STEP]
        for input_name, input_value in input_data.items():
            self.__model.setReal(
                [self.__names_to_references[input_name]], [input_value[0]]
            )

        self.__model.doStep(
            currentCommunicationPoint=self.__current_time,
            communicationStepSize=time_step,
        )

        self._time = array([self.__current_time + time_step])
        self._current_time = self._time[0]
        output_data = {}
        for output_name in self.get_output_data_names(with_namespaces=False):
            if output_name == self._TIME:
                output_data[self._TIME] = self._time
            else:
                output_data[output_name] = array(
                    self.__model.getReal([self.__names_to_references[output_name]])
                )
        self.store_local_data(**output_data)

    def __do_when_step_finished(self, time: float, recorder: Recorder) -> bool:
        """Callback to interact with the simulation after each time step.

        Try to change the values of the parameters passed as TimeSeries.

        Args:
            time: The current time.
            recorder: A helper to record the variables during the simulation.
        """
        fmu = recorder.fmu
        _time_id = 0
        for _time_id, time_value in enumerate(self.__time_series_time_steps[::-1]):
            if time > time_value:
                break

        for input_name in self.input_grammar.names:
            if input_name not in self.__parameters_as_time_series:
                continue

            fmu.setReal(
                [self.__names_to_references[input_name]],
                [self.local_data[input_name][-_time_id - 1]],
            )

        return True

    def __simulate_to_final_time(
        self, input_data: Mapping[str, NDArray[float]]
    ) -> None:
        """Simulate the FMU model from the current time to the final time.

        Args:
            input_data: The values of the FMU model inputs.
        """
        time_step = self.__simulation_settings[self._TIME_STEP]
        initial_time = self.__current_time
        final_time = initial_time + self.__simulation_settings[self._SIMULATION_TIME]
        if final_time > self._final_time:
            final_time = self._final_time
            LOGGER.warning("Stop the simulation at %s.", self._final_time)

        for input_name in self.input_grammar.names:
            if input_name not in self.__inputs_as_time_series:
                self.__model.setReal(
                    [self.__names_to_references[input_name]],
                    [self.local_data[input_name][0]],
                )

        result = simulate_fmu(
            self.__model_dir_path,
            start_time=initial_time,
            stop_time=final_time,
            input=self.__fmpy_input_time_series,
            solver=self.__solver_name,
            output_interval=1 if initial_time == final_time else (time_step or None),
            output=self.__output_names,
            fmu_instance=self.__model,
            model_description=self.__model_description,
            step_finished=self.__do_when_step_finished,
            initialize=False,
            terminate=False,
        )
        self._time = result[self._TIME]
        output_data = {
            output_name: result[output_name]
            for output_name in self.get_output_data_names(with_namespaces=False)
        }
        self.store_local_data(**output_data)
        self._current_time = final_time

    def __get_variables_set_with_time_series(self, causality: _Causality) -> list[str]:
        """Return the names of the variables set with time series.

        Args:
            causality: The causality to be checked.

        Returns:
            The names of the time series.
        """
        return [
            name
            for name in self.__names_to_time_series
            if name in self.__causalities_to_variable_names.get(causality, ())
        ]

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        super().__setstate__(state)
        self.__model = instantiate_fmu(
            self.__model_dir_path,
            self.__model_description,
            fmi_type=self.__model_type,
        )

    _ATTR_NOT_TO_SERIALIZE = MDODiscipline._ATTR_NOT_TO_SERIALIZE.union([
        "_BaseFMUDiscipline__model"
    ])
