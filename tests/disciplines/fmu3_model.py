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

from pythonfmu3 import Float64
from pythonfmu3 import Fmi3Causality
from pythonfmu3 import Fmi3Slave


class FMU3Model(Fmi3Slave):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.independent = 0.0
        self.parameter = 1.0
        self.output = 3.0
        self.register_variable(
            Float64("independent", causality=Fmi3Causality.independent)
        )
        self.register_variable(Float64("parameter", causality=Fmi3Causality.parameter))
        self.register_variable(Float64("output", causality=Fmi3Causality.output))

    def do_step(self, current_time, step_size):
        self.output += self.parameter
        return True
