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
"""The names of the variables used in the Sellar problem."""
from __future__ import annotations

from typing import Final

Y_1: Final[str] = "y_1"
r"""The name of the coupling variable $y_1$ computed by ``Sellar1``."""

Y_2: Final[str] = "y_2"
r"""The name of the coupling variable $y_2$ computed by ``Sellar2``."""

X_SHARED_1: Final[str] = "x_shared_1"
r"""The name of the 1st component of the design variable $x_{\textrm{shared}}$."""

X_SHARED_2: Final[str] = "x_shared_2"
r"""The name of the 2nd component of the design variable $x_{\textrm{shared}}$."""

X_LOCAL: Final[str] = "x_local"
r"""The name of the design variable $x_{\textrm{local}}$."""

OBJ: Final[str] = "obj"
r"""The name of the objective $\textrm{obj}$ computed by ``SellarSystem``."""

C_1: Final[str] = "c_1"
r"""The name of the 1st constraint $c_1$ computed by ``SellarSystem``."""

C_2: Final[str] = "c_2"
r"""The name of the 2nd constraint $c_2$ computed by ``SellarSystem``."""
