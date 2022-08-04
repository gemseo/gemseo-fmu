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
#        :author: Jorge CAMACHO CASERO:
#        :author: Francois Gallard:
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""Make a discipline from a Functional Mockup Unit (FMU) model."""
from __future__ import annotations

from pathlib import Path
from typing import Dict
from typing import Optional
from typing import Union

from gemseo.core.discipline import MDODiscipline
from numpy import array
from pyfmi import load_fmu


class FMUDiscipline(MDODiscipline):
    """Generic wrapper for Functional Mock-Up Units (FMUs).

    The FMUDiscipline is a wrapper for FMU models that generates a MDODiscipline from
    its inputs/outputs.
    It supports both model exchange (ME) and co-simulation (CS) models.
    This wrapper uses the `PyFMI library <https://jmodelica.org/pyfmi/>`_
    for loading and simulating the FMU model.

    Attributes:
        fmu_file_path (str): The FMU file.
        kind (str): The kind of model.
    """

    def __init__(
        self,
        fmu_file_path,  # type: Union[str, Path]
        kind="auto",  # type: str
        simulate_options=None,  # type: Optional[Dict[str, Union[int, str, float]]],
        history_outputs=None,  # type: Optional[Sequence[str]]
        name=None,  # type: Optional[str]
        input_grammar_file=None,  # type: Optional[Union[str, Path]]
        output_grammar_file=None,  # type: Optional[Union[str, Path]]
        auto_detect_grammar_files=False,  # type: bool
        grammar_type=MDODiscipline.JSON_GRAMMAR_TYPE,  # type: str
        cache_type=MDODiscipline.SIMPLE_CACHE,  # type: str
        cache_file_path=None,  # type: Optional[Union[str, Path]]
    ):  # type: (...) -> None # noqa: D205,D212,D415
        """
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
                        The options that should be used in the algorithm.
                        Default: Empty dict
            history_outputs: create a time history variable for the specified output.
                The name of each output variable is the output name followed by the
                suffix "_history". This option is deactivated by default.
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
            >>> discipline = FMUDiscipline(fmu_file_path, kind="CS",
            simulate_options=options)
            >>> # To get the available simulation options
            >>> discipline.get_available_simulate_options()
            >>> # To see the discipline information
            >>> print(discipline)
        """
        super().__init__(
            name,
            input_grammar_file,
            output_grammar_file,
            auto_detect_grammar_files,
            grammar_type,
            cache_type,
            cache_file_path,
        )
        # FMU model definition
        self.fmu_file_path = Path(fmu_file_path)
        self.kind = kind
        self.log_level = 2
        self._model = load_fmu(
            str(self.fmu_file_path), kind=self.kind, log_level=self.log_level
        )
        if history_outputs is None:
            history_outputs = []

        # Initialise the model
        # self._model.setup_experiment()
        # self._model.initialize()

        # Simulation options
        if simulate_options is None:
            simulate_options = {}
        self.simulate_options = simulate_options
        self.options = {}
        self._default_options = self._model.simulate_options()
        if "options" in self.simulate_options:
            self.options.update(self.simulate_options.pop("options"))

        self._check_simulate_options()

        # FMU Causality classification
        self._parameters = {}
        self._calculated_parameters = {}
        self._input_variables = {}
        self._output_variables = {}
        self._local_variables = {}
        self._independent_variables = {}
        self._unknown_variables = {}

        self._classify_model_variables_by_causality()

        # Discipline inputs must exclusively contain causalities of type input and of
        # type parameter. Non-numerical variables are filtered-out.
        self._unfiltered_data = self._input_variables.copy()
        self._unfiltered_data.update(self._parameters)
        self.input_data = {
            k: v
            for k, v in self._unfiltered_data.items()
            if isinstance(self._unfiltered_data[k][0], float)
        }

        # Time history variables
        self.history_outputs = history_outputs
        self.history_outputs_with_suffix = []
        for history_output in self.history_outputs:
            self.history_outputs_with_suffix.append(history_output + "_history")

        # Define input/output grammar and default inputs
        self.fmu_input_names = list(self.input_data.keys())
        self.fmu_output_names = list(self._output_variables.keys())

        self.input_grammar.initialize_from_data_names(self.fmu_input_names)
        self.output_grammar.initialize_from_data_names(
            self.fmu_output_names + self.history_outputs_with_suffix
        )
        self._default_inputs = self.input_data

        # Simulation results
        self._model_simulation_results = None

    def _check_simulate_options(self):  # type: (...) -> None
        """Check if the simulation options provided exists in PyFMI.

        Raises:
            ValueError: If the value provided by the user in simulate_options is not
                an existing option in PyFMI.
        """
        simulate_options = self._model.simulate_options()
        if not all([item in simulate_options for item in self.options]):
            msg = (
                "Not a PyFMI simulation option. "
                "Use the method get_available_simulate_options to get a list of "
                "available options"
            )
            raise ValueError(msg)

    def get_available_simulate_options(
        self,
    ):  # type: (...) -> Dict[str, Union[str,int,float]]
        """Return the model simulation options available in PyFMI."""
        return self._model.simulate_options()

    def _classify_model_variables_by_causality(self):  # type: (...) -> None
        """Classify the model variables by causality.

        (Parameter=0, Calculated Parameter=1, Input=2, Output=3, Local=4, Independent=5,
        Unknown=6)
        """
        for var in self._model.get_model_variables(causality=0):
            self._parameters[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=1):
            self._calculated_parameters[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=2):
            self._input_variables[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=3):
            self._output_variables[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=4):
            self._local_variables[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=5):
            self._independent_variables[var] = array(self._model.get(var))
        for var in self._model.get_model_variables(causality=6):
            self._unknown_variables[var] = array(self._model.get(var))

    @property
    def simulation_results(self):
        """Return the history of simulation results."""
        return self._model_simulation_results

    def __str__(self):  # type: (...) -> None
        s = f"""
            FMU model details:
            - Name: {self._model.get_name()}
            - Version: {self._model.get_version()}
            - Description: {self._model.get_description()}
            - Author: {self._model.get_author()}
            - Variables causality:"
                parameters:             {list(self._parameters.keys())}
                calculated_parameters:  {list(self._calculated_parameters.keys())}
                input_variables:        {list(self._input_variables.keys())}
                output_variables:       {list(self._output_variables.keys())}
                independent_variables:  {list(self._independent_variables.keys())}
                unknown_variables:      {list(self._unknown_variables.keys())}
            """

        s += "\nSimulation default options: "
        for key, val in self._default_options.items():
            s += f"\n- {key}: {val}"
        s += "\n"

        s += "\nUser-defined simulation options (override simulation default options):"
        for key, val in self.simulate_options.items():
            if key != "input":
                s += f"\n- {key}: {val}"
        for key, val in self.options.items():
            s += f"\n- {key}: {val}"
        s += "\n"

        s += "\nUser-defined inputs: "
        for key, val in self.simulate_options.items():
            if key == "input":
                s += f"\n- {self.simulate_options['input'][0]}"
        s += "\n"
        return s

    def _run(self):  # type: (...) -> None
        """Run the wrapper using the PyFMI library.

        This method gets the inputs from the input grammar, calls the pyFMI library for
        model simulation, and writes the simulation outputs to the output grammar.
        """
        for key, val in self.get_input_data().items():
            self._model.set(key, val)

        self._model_simulation_results = self._model.simulate(
            options=self.options, **self.simulate_options
        )

        for output_name in self.fmu_output_names:
            self.local_data[output_name] = array(
                [self._model_simulation_results.final(output_name)]
            )

        for output_name in self.history_outputs:
            self.local_data[output_name + "_history"] = self._model_simulation_results[
                output_name
            ]

        self._model.reset()
