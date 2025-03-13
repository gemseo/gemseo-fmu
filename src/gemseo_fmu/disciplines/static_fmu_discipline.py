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
"""A static discipline wrapping a Functional Mockup Unit (FMU) model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.utils.constants import READ_ONLY_EMPTY_DICT

from gemseo_fmu.disciplines.base_fmu_discipline import BaseFMUDiscipline

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from pathlib import Path


class StaticFMUDiscipline(BaseFMUDiscipline):
    """A static discipline wrapping a Functional Mockup Unit (FMU) model.

    This discipline relies on [FMPy](https://github.com/CATIA-Systems/FMPy).
    """

    _WARN_ABOUT_ZERO_TIME_STEP: ClassVar[bool] = False

    def __init__(  # noqa: D107
        self,
        file_path: str | Path,
        input_names: Iterable[str] | None = (),
        output_names: Iterable[str] = (),
        name: str = "",
        use_co_simulation: bool = True,
        model_instance_directory: str | Path = "",
        delete_model_instance_directory: bool = True,
        variable_names: Mapping[str, str] = READ_ONLY_EMPTY_DICT,
        validate: bool = True,
        **pre_instantiation_parameters: Any,
    ) -> None:
        super().__init__(
            file_path=file_path,
            input_names=input_names,
            output_names=output_names,
            name=name,
            use_co_simulation=use_co_simulation,
            model_instance_directory=model_instance_directory,
            delete_model_instance_directory=delete_model_instance_directory,
            do_step=True,
            add_time_to_output_grammar=False,
            variable_names=variable_names,
            validate=validate,
            **pre_instantiation_parameters,
        )
