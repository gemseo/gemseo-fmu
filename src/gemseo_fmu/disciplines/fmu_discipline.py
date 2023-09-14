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
"""A discipline wrapping a Functional Mockup Unit (FMU) model."""
from __future__ import annotations

import logging
from pathlib import Path
from shutil import rmtree
from types import MappingProxyType
from typing import Any
from typing import Final
from typing import Iterable
from typing import Mapping
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
from fmpy.model_description import DefaultExperiment
from fmpy.model_description import ModelDescription
from fmpy.simulation import Recorder
from fmpy.util import fmu_info
from gemseo.core.discipline import MDODiscipline
from numpy import array
from numpy import double
from numpy import interp
from numpy import ndarray
from numpy import vstack
from numpy.typing import NDArray
from strenum import StrEnum

from gemseo_fmu.disciplines.time_series import TimeSeries

FMUModel = Union[FMU1Model, FMU2Model, FMU3Model, FMU1Slave, FMU2Slave, FMU3Slave]

LOGGER = logging.getLogger(__name__)


class FMUDiscipline(MDODiscipline):
    """A discipline wrapping a Functional Mockup Unit (FMU) model.

    This discipline relies on `FMPy <https://github.com/CATIA-Systems/FMPy>`__.

    Notes:
        The time series are interpolated at the time steps
        resulting from the union of their respective time steps.
        Then,
        between two time steps,
        the time series for the variables of causality "input" are linearly interpolated
        at the *integration* time steps
        while for the variables of causality "parameter",
        the time series are considered as constant.
    """

    class _Constants(StrEnum):
        """String constants."""

        CO_SIMULATION = "CoSimulation"
        FINAL_TIME = "final_time"
        INITIAL_TIME = "initial_time"
        MODEL_EXCHANGE = "ModelExchange"
        RESTART = "restart"
        SIMULATION_TIME = "simulation_time"
        TIME = "time"
        TIME_STEP = "time_step"
        INPUT = "input"
        PARAMETER = "parameter"

    __TIME: Final[str] = _Constants.TIME.value

    __fmu_file_path: Path
    """The path to the FMU file, which is a ZIP archive."""

    __delete_fmu_instance_directory: bool
    """Whether trying to delete the directory of the FMU instance when deleting the
    discipline."""

    __fmu_model_dir_path: Path
    """The description of the FMU model, read from the XML file in the archive."""

    __fmu_model_description: ModelDescription
    """The description of the FMU model."""

    __causalities_to_variable_names: dict[str, list[str]]
    """The names of the variables sorted by causality."""

    __fmu_model_name: str
    """The name of the FMU model."""

    __fmu_model_fmi_version: str
    """The FMI version of the FMU model."""

    __fmu_model: FMUModel
    """The FMU model."""

    __names_to_references: dict[str, int]

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
    """The FMU inputs passed as :class:`.TimeSeries` at the last execution."""

    __parameters_as_time_series: list[str]
    """The FMU parameters passed as :class:`.TimeSeries` at the last execution."""

    __time_series_time_steps: NDArray[float]
    """The time steps of the time series after pre-processing of the original ones."""

    __fmpy_input_time_series: NDArray[float] | None
    """The fmpy-formatted input time series."""

    __initial_values: dict[str, NDArray[float]]
    """The initial values of the discipline outputs."""

    _initial_time: float
    """The initial time."""

    _final_time: float
    """The final time."""

    def __init__(
        self,
        fmu_file_path: str | Path,
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
        solver_name: str = "CVode",
        fmu_instance_directory: str | Path = "",
        delete_fmu_instance_directory: bool = True,
        **pre_instantiation_parameters: Any,
    ) -> None:
        """
        Args:
            fmu_file_path: The path to the FMU model file.
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
                when calling :meth:`.execute`.
                Otherwise, simulate the model from ``initial_time`` to ``final_time``.
            use_co_simulation: Whether the co-simulation FMI type is used.
                Otherwise, use model-exchange FMI type.
                When ``do_step`` is ``True``, the co-simulation FMI type is required.
            solver_name: The name of the solver to simulate a model-exchange model.
            fmu_instance_directory: The directory of the FMU instance,
                containing the files extracted from the FMU model file;
                if empty, let ``fmpy`` create a temporary directory.
            delete_fmu_instance_directory: Whether to delete the directory
                of the FMU instance when deleting the discipline.
            **pre_instantiation_parameters: The parameters to be passed
                to :meth:`._pre_instantiate`.
        """  # noqa: D205 D212 D415
        self.__delete_fmu_instance_directory = delete_fmu_instance_directory

        # The path to the FMU file, which is a ZIP archive.
        self.__fmu_file_path = Path(fmu_file_path)

        # The path to unzipped archive.
        self.__fmu_model_dir_path = Path(
            extract(str(fmu_file_path), unzipdir=fmu_instance_directory or None)
        ).resolve()

        # The description of the FMU model, read from the XML file in the archive.
        self.__fmu_model_description = read_model_description(self.__fmu_model_dir_path)

        all_input_names = []
        all_output_names = []
        self.__causalities_to_variable_names = {}
        for variable in self.__fmu_model_description.modelVariables:
            causality = variable.causality
            if causality not in self.__causalities_to_variable_names:
                self.__causalities_to_variable_names[causality] = []

            self.__causalities_to_variable_names[causality].append(variable.name)

        self.__fmu_model_name = self.__fmu_model_description.modelName
        self.__fmu_model_fmi_version = self.__fmu_model_description.fmiVersion

        for variable in self.__fmu_model_description.modelVariables:
            if variable.causality in ["input", "parameter"]:
                all_input_names.append(variable.name)
            elif variable.causality == "output":
                all_output_names.append(variable.name)

        output_names = output_names or all_output_names
        if input_names is None:
            input_names = []
        else:
            input_names = input_names or all_input_names

        # The type of FMI.
        self.__fmu_model_type = (
            self._Constants.CO_SIMULATION
            if use_co_simulation
            else self._Constants.MODEL_EXCHANGE
        )
        if do_step and not use_co_simulation:
            LOGGER.warning(
                "The FMUDiscipline requires a co-simulation model when do_step is True."
            )
            self.__fmu_model_type = self._Constants.CO_SIMULATION

        # The FMU model.
        self.__fmu_model = instantiate_fmu(
            self.__fmu_model_dir_path,
            self.__fmu_model_description,
            fmi_type=self.__fmu_model_type,
        )

        # The value references related to the variables names.
        self.__names_to_references = {
            variable.name: variable.valueReference
            for variable in self.__fmu_model_description.modelVariables
        }

        # The names of the FMU model outputs of interest.
        self.__fmu_model_output_names = output_names

        # The different times of interest.
        if initial_time is None:
            self._initial_time = self.__get_default_time_value(
                self.__fmu_model_description.defaultExperiment, "startTime", 0.0
            )
        else:
            self._initial_time = initial_time

        self.__current_time = self._initial_time

        if final_time is None:
            self._final_time = self.__get_default_time_value(
                self.__fmu_model_description.defaultExperiment,
                "stopTime",
                self._initial_time,
            )
        else:
            self._final_time = final_time

        self.__time_step = time_step

        # Initialize the FMU model.
        pre_instantiation_parameters = pre_instantiation_parameters or {}
        self._pre_instantiate(**pre_instantiation_parameters)
        self.__fmu_model.setupExperiment(startTime=self._initial_time)
        self.__fmu_model.enterInitializationMode()
        self.__fmu_model.exitInitializationMode()

        # Store the initial values of the discipline outputs,
        # namely model outputs and time.
        self.__initial_values = {
            output_name: array(
                self.__fmu_model.getReal([self.__names_to_references[output_name]])
            )
            for output_name in self.__fmu_model_output_names
        }
        self.__initial_values[self.__TIME] = array([self._initial_time])

        # Whether to execute step by step.
        self.__do_step = do_step

        # The numerical solver to simulate the FMU model
        self.__solver_name = solver_name

        # Define the default values of the simulation settings.
        self.__default_simulation_settings = {
            self._Constants.RESTART: restart,
            self._Constants.TIME_STEP: self.__time_step,
        }
        if not do_step:
            self.__default_simulation_settings[self._Constants.SIMULATION_TIME] = (
                self._final_time - self._initial_time
            )
        self.__simulation_settings = {}

        # Make the object a MDODiscipline.
        name = name or self.__fmu_model_description.modelName or self.__class__.__name__
        super().__init__(
            name=name,
            cache_type=self.CacheType.NONE,
        )

        # Define the grammars of the model inputs and model outputs.
        self.input_grammar.update_from_names(input_names)
        self.output_grammar.update_from_names(output_names)
        self.__use_time_in_output_grammar = add_time_to_output_grammar
        if add_time_to_output_grammar:
            self.output_grammar.update_from_names([self.__TIME])
            self.output_grammar.add_namespace(self.__TIME, name)

        # Set the default values of the inputs and update the initial values.
        self.default_inputs = {
            input_name: array(
                self.__fmu_model.getReal([self.__names_to_references[input_name]])
            )
            for input_name in input_names
        }
        self.__initial_values.update(self.default_inputs)

        # Store the initial output values in the local data.
        self.local_data.update(self.__initial_values)

        # The time steps of the last execution; None when not yet executed.
        self.__time = None

        self.__names_to_time_series = {}
        self.__fmpy_input_time_series = None

    @staticmethod
    def __get_default_time_value(
        default_experiment: DefaultExperiment, field: str, default_value: float
    ) -> float:
        """Get the default value of a time.

        Args:
            default_experiment: The default experiment.
            field: The field of the experiment defining the time.
            default_value: The default value if ``experiment`` is ``None``
                or its field is ``None``.

        Returns:
            The default value of the time.
        """
        if default_experiment is None:
            return default_value

        value = getattr(default_experiment, field)
        if value is None:
            return default_value

        return float(value)

    @property
    def fmu_model_description(self) -> ModelDescription:
        """The description of the FMU model."""
        return self.__fmu_model_description

    @property
    def fmu_model(self) -> FMUModel:
        """The FMU model."""
        return self.__fmu_model

    @property
    def causalities_to_variable_names(self) -> dict[str, list[str]]:
        """The names of the variables sorted by causality."""
        return self.__causalities_to_variable_names

    @property
    def initial_values(self) -> dict[str, NDArray[float]]:
        """The initial input, output and time values."""
        return self.__initial_values

    @property
    def time(self) -> NDArray[float] | None:
        """The time steps of the last execution if any."""
        return self.__time

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + "\n"
            + fmu_info(self.__fmu_file_path, ["input", "parameter", "output"])
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
        full_input_data = self._filter_inputs(input_data)
        self.__names_to_time_series = {
            name: value
            for name, value in full_input_data.items()
            if isinstance(value, TimeSeries)
        }
        self.__inputs_as_time_series = [
            name
            for name in self.__names_to_time_series
            if self.__check_name_causality(name, self._Constants.INPUT)
        ]
        self.__parameters_as_time_series = [
            name
            for name in self.__names_to_time_series
            if self.__check_name_causality(name, self._Constants.PARAMETER)
        ]
        self.__time_series_time_steps = array([self.__current_time])
        if self.__names_to_time_series:
            self.__time_series_time_steps = time = array(
                sorted(
                    set.union(
                        *[set(ts.time) for ts in self.__names_to_time_series.values()]
                    )
                )
            )
            for ts in self.__names_to_time_series.values():
                ts.observable = interp(time, ts.time, ts.observable)

            values = vstack(
                [time]
                + [
                    self.__names_to_time_series[name].observable
                    for name in self.__inputs_as_time_series
                ]
            )
            full_input_data.update(
                {
                    name: tuple(ts.observable)
                    for name, ts in self.__names_to_time_series.items()
                }
            )
            if len(values) > 1:
                self.__fmpy_input_time_series = array(
                    [tuple(row) for row in values.T],
                    dtype=[(self.__TIME, double)]
                    + [(name, double) for name in self.__inputs_as_time_series],
                )
        return super().execute(full_input_data)

    def set_next_execution(
        self,
        restart: bool | None = None,
        simulation_time: float | None = None,
        time_step: float | None = None,
    ) -> None:
        """Change the simulation settings for the next call to :meth:`.execute`.

        Args:
            time_step: The time step of the simulation;
                if ``None``, use the value passed at the instantiation.
            restart: Whether to restart the model at ``initial_time``
                before executing it;
                if ``None``, use the value passed at the instantiation.
            simulation_time: The duration of the simulation;
                if ``None``, execute until the final time.
        """  # noqa: D205 D212 D415
        self.__simulation_settings = self.__default_simulation_settings.copy()
        if time_step is not None:
            self.__simulation_settings[self._Constants.TIME_STEP] = time_step

        if restart is not None:
            self.__simulation_settings[self._Constants.RESTART] = restart

        if simulation_time is not None:
            self.__simulation_settings[
                self._Constants.SIMULATION_TIME
            ] = simulation_time

    def _run(self) -> None:
        if not self.__simulation_settings:
            self.__simulation_settings = self.__default_simulation_settings

        input_data = self.get_input_data(with_namespaces=False)
        if self.__simulation_settings[self._Constants.RESTART]:
            self._current_time = self._initial_time
            self.__fmu_model.reset()
            self.__fmu_model.enterInitializationMode()
            self.__fmu_model.exitInitializationMode()

        if self._initial_time < self._current_time == self._final_time:
            raise ValueError(
                "The discipline cannot be executed "
                f"as the current time is the final time ({self._current_time})."
            )

        if self.__do_step:
            self.__simulate_one_time_step(input_data)
        else:
            self.__simulate_to_final_time(input_data)

        self.__simulation_settings = {}

    def __del__(self) -> None:
        self.__fmu_model.terminate()
        self.__fmu_model.freeInstance()
        if self.__delete_fmu_instance_directory:
            rmtree(self.__fmu_model_dir_path, ignore_errors=True)

    def __simulate_one_time_step(
        self, input_data: Mapping[str, NDArray[float]]
    ) -> None:
        """Simulate the FMU model during a single time step.

        Args:
            input_data: The values of the FMU model inputs.
        """
        time_step = self.__simulation_settings[self._Constants.TIME_STEP]
        for input_name, input_value in input_data.items():
            self.__fmu_model.setReal(
                [self.__names_to_references[input_name]], [input_value[0]]
            )

        self.__fmu_model.doStep(
            currentCommunicationPoint=self._current_time,
            communicationStepSize=time_step,
        )

        self.__time = array([self._current_time + time_step])
        self._current_time = self.__time[0]
        output_data = {}
        for output_name in self.get_output_data_names(with_namespaces=False):
            if output_name == self.__TIME:
                output_data[self.__TIME] = self.__time
            else:
                output_data[output_name] = array(
                    self.__fmu_model.getReal([self.__names_to_references[output_name]])
                )
        self.store_local_data(**output_data)

    def __simulate_to_final_time(
        self, input_data: Mapping[str, NDArray[float]]
    ) -> None:
        """Simulate the FMU model from the current time to the final time.

        Args:
            input_data: The values of the FMU model inputs.
        """
        time_step = self.__simulation_settings[self._Constants.TIME_STEP]
        initial_time = self._current_time
        final_time = (
            initial_time + self.__simulation_settings[self._Constants.SIMULATION_TIME]
        )
        if final_time > self._final_time:
            final_time = self._final_time
            LOGGER.warning("Stop the simulation at %s.", self._final_time)

        def do_when_step_finished(time: float, recorder: Recorder) -> bool:
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

        for input_name in self.input_grammar.names:
            if input_name not in self.__inputs_as_time_series:
                self.__fmu_model.setReal(
                    [self.__names_to_references[input_name]],
                    [self.local_data[input_name][0]],
                )

        result = simulate_fmu(
            self.__fmu_model_dir_path,
            start_time=initial_time,
            stop_time=final_time,
            input=self.__fmpy_input_time_series,
            solver=self.__solver_name,
            output_interval=time_step or 1.0,
            step_size=time_step,
            output=self.__fmu_model_output_names,
            fmu_instance=self.__fmu_model,
            model_description=self.__fmu_model_description,
            step_finished=do_when_step_finished,
            initialize=False,
            terminate=False,
        )
        self.__time = result[self.__TIME]
        output_data = {
            output_name: result[output_name]
            for output_name in self.get_output_data_names(with_namespaces=False)
        }
        self.store_local_data(**output_data)

        self._current_time = final_time

    def __check_name_causality(self, name: str, causality: str) -> bool:
        """Check the causality of a variable from its name.

        Args:
            name: The name of the variable.
            causality: The causality to be checked.

        Returns:
            Whether the variable has the given causality
        """
        return name in self.__causalities_to_variable_names.get(causality, ())
