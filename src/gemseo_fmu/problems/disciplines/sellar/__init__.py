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

$$
\begin{aligned}
\text{minimize the objective function }&obj=x_{\textrm{local}}^2 + x_{\textrm{shared},2}
+y_1^2+e^{-y_2} \\
\text{with respect to the design variables }&x_{\textrm{shared}},\,x_{\textrm{local}} \\
\text{subject to the general constraints }
& c_1 \leq 0\\
& c_2 \leq 0\\
\text{subject to the bound constraints }
& -10 \leq x_{\textrm{shared},1} \leq 10\\
& 0 \leq x_{\textrm{shared},2} \leq 10\\
& 0 \leq x_{\textrm{local}} \leq 10.
\end{aligned}
$$

where the coupling variables are

$$
\text{Discipline 1: } y_1 =
\sqrt{x_{\textrm{shared},1}^2 + x_{\textrm{shared},2} + x_{\textrm{local}} - 0.2\,y_2},
$$

and

$$\text{Discipline 2: }y_2 = |y_1| + x_{\textrm{shared},1} + x_{\textrm{shared},2}.$$

and where the general constraints are

$$c_1 = 3.16 - y_1^2$$

and

$$c_2 = y_2 - 24.$$

This package implements three disciplines
to compute the different coupling variables, constraints and objective:

- [FMUSellar1][gemseo_fmu.problems.disciplines.sellar.sellar_1.FMUSellar1]:
  this [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  computes $y_1$
  from $y_2$, $x_{\textrm{shared},1}$, $x_{\textrm{shared},2}$ and $x_{\textrm{local}}$.
- [FMUSellar2][gemseo_fmu.problems.disciplines.sellar.sellar_2.FMUSellar2]:
  this [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  computes $y_2$
  from $y_1$, $x_{\textrm{shared},1}$ and $x_{\textrm{shared},2}$.
- [FMUSellarSystem][gemseo_fmu.problems.disciplines.sellar.sellar_system.FMUSellarSystem]:
  this [FMUDiscipline][gemseo_fmu.disciplines.fmu_discipline.FMUDiscipline]
  computes both objective and constraints
  from $y_1$, $y_2$, $x_{\textrm{local}}$ and $x_{\textrm{shared},2}$.
"""
from __future__ import annotations
