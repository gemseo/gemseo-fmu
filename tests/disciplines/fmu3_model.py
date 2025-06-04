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

from enum import Enum

from numpy import array
from numpy import roll
from pythonfmu3 import Boolean
from pythonfmu3 import Dimension
from pythonfmu3 import Enumeration
from pythonfmu3 import EnumerationType
from pythonfmu3 import Float64
from pythonfmu3 import Fmi3Causality
from pythonfmu3 import Fmi3Slave
from pythonfmu3 import Int32
from pythonfmu3 import Int64
from pythonfmu3 import String


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


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
        self.vector = array([0.0, 1.0, 2.0, 3.0, 4.0])
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

        # The remaining variables are used by tests to check variable type management.
        self.int32 = 6
        self.int64 = 7
        self.float64 = 7.23
        self.boolean = True
        self.string = "foo"
        self.enumeration = Color.RED
        self.register_variable(Int32("int32", causality=Fmi3Causality.input))
        self.register_variable(Int64("int64", causality=Fmi3Causality.input))
        self.register_variable(Float64("float64", causality=Fmi3Causality.input))
        self.register_variable(Boolean("boolean", causality=Fmi3Causality.input))
        self.register_variable(String("string", causality=Fmi3Causality.input))
        self.register_variable(
            Enumeration(
                "enumeration",
                declared_type="Color",
                causality=Fmi3Causality.input,
                getter=lambda: self.enumeration.value,
                setter=lambda v: setattr(self, "enumeration", Color(v)),
            ),
            var_type=EnumerationType("Color", values=Color),
        )

    def exit_initialization_mode(self):
        self.output = 3.0 + self.increment * self.input

    def do_step(self, current_time, step_size):
        self.output += self.increment
        self.vector = roll(self.vector, 1)
        return True
