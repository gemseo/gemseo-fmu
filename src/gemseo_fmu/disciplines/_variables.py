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
"""Utils."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from collections.abc import Iterable
from typing import Any
from typing import Generic
from typing import TypeVar

from gemseo.utils.metaclasses import ABCGoogleDocstringInheritanceMeta
from numpy import atleast_1d

T = TypeVar(
    "T",
    bound=Callable[[Iterable[int]], list[float]]
    | Callable[[Iterable[int], int], list[float]],
)


class FMUTimeVariable:
    """The FMU variable defining the time."""

    disciplinary_name: str
    """The name of the time variable in the discipline."""

    initial: Any
    """The initial value of the variable."""

    name: str
    """The name of the time variable in the FMU."""

    def __init__(self, name: str, disciplinary_name: str) -> None:
        """
        Args:
            name: The name of the time variable in the FMU.
            disciplinary_name: The name of the time variable in the discipline.
        """  # noqa: D205 D212
        self.name = name
        self.disciplinary_name = disciplinary_name
        self.initial = None


class BaseFMUVariable(
    FMUTimeVariable, Generic[T], metaclass=ABCGoogleDocstringInheritanceMeta
):
    """A base helper for editing the variable of an FMU."""

    _getter: T
    """The FMU's callable to get the value."""

    __setter: Callable[[Iterable[int], Iterable[Any]], None]
    """The FMU's callable to set the value."""

    reference: int
    """The value reference of the variable in the FMU."""

    def __init__(
        self,
        name: str,
        disciplinary_name: str,
        getter: T,
        setter: Callable[[Iterable[int], Iterable[Any]], None],
        reference: int,
    ) -> None:
        """
        Args:
            getter: The FMU's method to get the value.
            setter: The FMU's method to set the value.
            reference: The value reference of the variable in the FMU.
        """  # noqa: D205 D212
        super().__init__(name, disciplinary_name)
        self._getter = getter
        self.__setter = setter
        self.reference = reference
        self.time_function = None

    @abstractmethod
    def get_value(self) -> Any:
        """Return the value of the variable.

        Returns:
            The value of the variable.
        """

    def set_value(self, value: Any) -> Any:
        """Set the value of the variable.

        Args:
            value: The value of the variable.
        """
        self.__setter([self.reference], atleast_1d(value))


class RealVariable(BaseFMUVariable[Callable[[Iterable[int]], list[float]]]):
    """An helper for editing the variable of an FMU with FMI 1 or 2."""

    def get_value(self) -> list[float]:
        return self._getter([self.reference])


class FMU3Variable(BaseFMUVariable[Callable[[Iterable[int], int], list[float]]]):
    """An helper for editing the variable of an FMU with FMI 3."""

    __size: int
    """The size of the variable."""

    def __init__(
        self,
        name: str,
        disciplinary_name: str,
        getter: Callable[[Iterable[int], int], list[Any]],
        setter: Callable[[Iterable[int], Iterable[Any]], None],
        reference: int,
        size: int,
    ) -> None:
        """
        Args:
            size: The size of the variable.
        """  # noqa: D205 D212
        super().__init__(name, disciplinary_name, getter, setter, reference)
        self.__size = size

    def get_value(self) -> list[Any]:
        return self._getter([self.reference], self.__size)
