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
r"""FMU disciplines of the Sellar use case.

Use case proposed by Sellar et al. in

Sellar, R., Batill, S., & Renaud, J. (1996).
Response surface based, concurrent subspace optimization
for multidisciplinary system design.
In 34th aerospace sciences meeting and exhibit (p. 714).

The MDO problem is written as follows:

.. math::

   \begin{aligned}
   \text{minimize the objective function }&obj=x_{local}^2 + x_{shared,2}
   +y_1^2+e^{-y_2} \\
   \text{with respect to the design variables }&x_{shared},\,x_{local} \\
   \text{subject to the general constraints }
   & c_1 \leq 0\\
   & c_2 \leq 0\\
   \text{subject to the bound constraints }
   & -10 \leq x_{shared,1} \leq 10\\
   & 0 \leq x_{shared,2} \leq 10\\
   & 0 \leq x_{local} \leq 10.
   \end{aligned}

where the coupling variables are

.. math::

    \text{Discipline 1: } y_1 = \sqrt{x_{shared,1}^2 + x_{shared,2} +
     x_{local} - 0.2\,y_2},

and

.. math::

    \text{Discipline 2: }y_2 = |y_1| + x_{shared,1} + x_{shared,2}.

and where the general constraints are

.. math::

   c_1 = 3.16 - y_1^2

   c_2 = y_2 - 24

This package implements three disciplines
to compute the different coupling variables, constraints and objective:

- :class:`.FMUSellar1`:
  this :class:`.MDODiscipline` computes :math:`y_1`
  from :math:`y_2`, :math:`x_{shared,1}`, :math:`x_{shared,2}` and :math:`x_{local}`.
- :class:`.FMUSellar2`:
  this :class:`.MDODiscipline` computes :math:`y_2`
  from :math:`y_1`, :math:`x_{shared,1}` and :math:`x_{shared,2}`.
- :class:`.FMUSellarSystem`:
  this :class:`.MDODiscipline` computes both objective and constraints
  from :math:`y_1`, :math:`y_2`, :math:`x_{local}` and :math:`x_{shared,2}`.
"""
from __future__ import annotations
