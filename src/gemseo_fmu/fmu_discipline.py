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
#    INITIAL AUTHORS - initial API and implementation and/or initial documentation
#        :author: Jorge CAMACHO CASERO:
#        :author: Francois Gallard:
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""Make a discipline from a Functional Mockup Unit (FMU) model."""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar
from typing import Sequence

from gemseo.core.discipline import MDODiscipline
from numpy import array
from pyfmi import FMUModel
from pyfmi import load_fmu


class FMUDiscipline(MDODiscipline):
    """Generic wrapper for Functional Mock-Up Units (FMUs).

    This discipline wraps a FMU model and computes some of its outputs from some of
    its inputs.
    It supports both model exchange (ME) and co-simulation (CS) models.
    This wrapper uses the `PyFMI library <https://jmodelica.org/pyfmi/>`_
    for loading and simulating the FMU model.

    Examples:
        >>> # Create a discipline considering PyFMI default simulation options
        >>> discipline = FMUDiscipline(fmu_file_path, kind="CS")
        >>> # Create a discipline considering user-defined simulation options
        >>> options = {
        >>>    "start_time": 0.0,
        >>>    "final_time": 1.0,
        >>>    "algorithm": "FMICSAlg",
        >>>    "options": {"ncp": 510, "initialize": True},
        >>>}
        >>> discipline = FMUDiscipline(fmu_file_path, "CS", options)
        >>> # To get the available simulation options
        >>> discipline.simulation_options()
        >>> # To see the discipline information
        >>> print(discipline)
    """

    LOG_LEVEL: ClassVar[int] = 0
    """The log level of the model.

    Available values:
    - NOTHING = 0
    - FATAL = 1
    - ERROR = 2
    - WARNING = 3
    - INFO = 4
    - VERBOSE = 5
    - DEBUG = 6
    - ALL = 7
    """

    SILENT_PYFMI_CS: ClassVar[bool] = True
    """Whether to disable the PyFMI log on console. The default is ``True``."""

    model: FMUModel
    """The PyFMI model."""

    def __init__(
        self,
        fmu_file_path: str | Path,
        kind: str = "auto",
        simulate_options: dict[str, int | str | float] | None = None,
        history_outputs: Sequence[str] | None = None,
        name: str | None = None,
    ) -> None:
        """# noqa: D205,D212,D415
        Args:
            fmu_file_path: The path to the FMU file.
            kind: The kind of model.
                This is only needed if a FMU contains both a ME and CS model.
                Available options: 'ME', 'CS', 'auto'
            simulate_options: The PyFMI simulation options.
                The simulation method depends on which algorithm is used,
                this can be set with the function argument 'algorithm'.
                Options for the algorithm are passed as option classes or as pure dicts.
                The default algorithm for this function is FMICSAlg.

                Simulation Options Parameters:

                    - start_time --
                        Start time for the simulation.
                        Default: Start time defined in the default experiment from
                                the ModelDescription file.

                    - final_time --
                        Final time for the simulation.
                        Default: Stop time defined in the default experiment from
                                the ModelDescription file.

                    - input --
                        Input signal for the simulation. The input should be a 2-tuple
                        consisting of first the names of the input variable(s) and then
                        the data matrix.
                        Default: Empty tuple.

                    - algorithm --
                        The algorithm which will be used for the simulation is specified
                        by passing the algorithm class as string or class object in this
                        argument. 'algorithm' can be any class which implements the
                        abstract class AlgorithmBase (found in algorithm_drivers.py). In
                        this way it is possible to write own algorithms and use them
                        with this function.
                        Default: 'FMICSAlg'

                    - options --
                        The available PyFMI options that should be used in the
                        algorithm.
                        See method 'get_available_simulate_options()'
                        Default: Empty dict
            history_outputs: create a time history variable for the specified output.
                The name of each output variable is the output name followed by the
                suffix "_history". This option is deactivated by default.
        """
        super().__init__(name=name)

        # FMU model definition
        self._fmu_file_path = Path(fmu_file_path)
        self._kind = kind
        self.model = load_fmu(
            str(self._fmu_file_path), kind=self._kind, log_level=self.LOG_LEVEL
        )
        self.__reset_fmu = True

        self._simulate_options = simulate_options or {}
        self.__pyfmi_options = {}
        self.__default_options = self.model.simulate_options()
        if self.SILENT_PYFMI_CS is True and self._kind == "CS":
            self.__pyfmi_options["silent_mode"] = self.SILENT_PYFMI_CS
        if "pyfmi_options" in self._simulate_options:
            self.__pyfmi_options.update(self._simulate_options.pop("pyfmi_options"))

        self.__check_simulate_options()

        # FMU Causality classification
        self.__parameters = {}
        self.__calculated_parameters = {}
        self.__input_variables = {}
        self.__output_variables = {}
        self.__local_variables = {}
        self.__independent_variables = {}
        self.__unknown_variables = {}

        self.__classify_model_variables_by_causality()

        # Discipline inputs must exclusively contain causalities of type input and of
        # type parameter.
        # Non-numerical variables are filtered-out.
        self._unfiltered_data = self.__input_variables.copy()
        self._unfiltered_data.update(self.__parameters)
        self.input_data = {
            k: v
            for k, v in self._unfiltered_data.items()
            if isinstance(self._unfiltered_data[k][0], float)
        }
        self.default_inputs = self.input_data

        history_outputs = history_outputs or []
        self.__history_outputs = history_outputs
        self.__history_outputs_with_suffix = []
        for history_output in self.__history_outputs:
            self.__history_outputs_with_suffix.append(f"{history_output}_history")

        # Define input/output grammar and default inputs
        self.__fmu_input_names = list(self.input_data.keys())
        self.__fmu_output_names = list(self.__output_variables.keys())

        self.input_grammar.update(self.__fmu_input_names)
        self.output_grammar.update(
            self.__fmu_output_names + self.__history_outputs_with_suffix
        )

        self.__model_simulation_results = {}

    def __check_simulate_options(self) -> None:
        """Check if the simulation options provided are PyFMI options.

        Raises:
            ValueError: When a simulation option is not a PyFMI option.
        """
        if not set(self.__pyfmi_options).issubset(self.model.simulate_options()):
            msg = (
                "Some simulation options are no PyFMI simulation option. "
                "See simulation_options()."
            )
            raise ValueError(msg)

    def __classify_model_variables_by_causality(self) -> None:
        """Classify the model variables by causality.

        - Parameter = 0
        - Calculated Parameter = 1
        - Input = 2
        - Output = 3
        - Local = 4
        - Independent = 5
        - Unknown = 6
        """
        # Model initialization is required to access the model variables.
        # An independent object is created here to avoid conflicts with the original
        # model.
        _fmu_model = load_fmu(self._fmu_file_path)
        _fmu_model.initialize()

        causalities = (
            self.__parameters,
            self.__calculated_parameters,
            self.__input_variables,
            self.__output_variables,
            self.__local_variables,
            self.__independent_variables,
            self.__unknown_variables,
        )

        for causality, variables in enumerate(causalities):
            for var in _fmu_model.get_model_variables(causality=causality):
                variables[var] = array(_fmu_model.get(var))

    @property
    def simulation_options(self) -> dict[str, str | int | float]:
        """The PyFMI simulation options."""
        return self.model.simulate_options()

    @property
    def simulation_results(self) -> dict[str, float]:
        """The history of simulation results."""
        return self.__model_simulation_results

    def __repr__(self) -> str:
        s = f"""
\nFMU model details:
    - Name: {self.model.get_name()}
    - Version: {self.model.get_version()}
    - Description: {self.model.get_description()}
    - Author: {self.model.get_author()}
    - Variables causality:
            parameters:             {list(self.__parameters.keys())}
            calculated_parameters:  {list(self.__calculated_parameters.keys())}
            input_variables:        {list(self.__input_variables.keys())}
            output_variables:       {list(self.__output_variables.keys())}
            independent_variables:  {list(self.__independent_variables.keys())}
            unknown_variables:      {list(self.__unknown_variables.keys())}
"""

        s += "\nSimulation default options (from PyFMI): "
        for key, val in self.__default_options.items():
            s += f"\n    - {key}: {val}"
        s += "\n"

        s += "\nSimulation options (override simulation default options):"
        for key, val in self._simulate_options.items():
            if key != "input":
                s += f"\n    - {key}: {val}"
        for key, val in self.__pyfmi_options.items():
            s += f"\n    - {key}: {val}"
        s += "\n"
        s += "\nUser-defined inputs: "
        for key in self._simulate_options.keys():
            if key == "input":
                s += f"\n    - {self._simulate_options['input'][0]}"
        s += "\n"
        return s

    def _run(self) -> None:
        for key, val in self.get_input_data().items():
            self.model.set(key, val)

        self.__model_simulation_results = self.model.simulate(
            options=self.__pyfmi_options, **self._simulate_options
        )

        for output_name in self.__fmu_output_names:
            self.local_data[output_name] = array(
                [self.__model_simulation_results.final(output_name)]
            )

        for output_name in self.__history_outputs:
            self.local_data[f"{output_name}_history"] = self.__model_simulation_results[
                output_name
            ]

        # Reset the model: needed for performing a new simulation
        if self.__reset_fmu:
            self.model.reset()
