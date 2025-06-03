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
"""This module is used to generate an FMU3 model using pythonfmu3."""

import numpy as np
from pythonfmu3 import Dimension
from pythonfmu3 import Float64
from pythonfmu3 import Fmi3Causality
from pythonfmu3 import Fmi3Slave


class FMU3Model(Fmi3Slave):
    """An FMU model using the FMI3 standard.

    At each integration step,
    ``output`` (causality: output) is increased
    by one ``increment`` (default: 1.0, causality: parameter).

    When exiting the initialization mode,
    ``output`` is set to ``3 + increment * input``
    where the default value of ``input`` (causality: input) is 0.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.independent = 0.0
        self.input = 0.0
        self.output = 3.0
        self.increment = 1.0
        self.vector = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        self.register_variable(
            Float64("independent", causality=Fmi3Causality.independent)
        )
        self.register_variable(Float64("input", causality=Fmi3Causality.input))
        self.register_variable(Float64("increment", causality=Fmi3Causality.parameter))
        self.register_variable(Float64("output", causality=Fmi3Causality.output))
        self.register_variable(
            Float64(
                "vector",
                causality=Fmi3Causality.output,
                dimensions=[Dimension(start="5")],
            )
        )

    def exit_initialization_mode(self):
        self.output = 3.0 + self.increment * self.input

    def do_step(self, current_time, step_size):
        self.output += self.increment
        self.vector = np.roll(self.vector, 1)
        return True
