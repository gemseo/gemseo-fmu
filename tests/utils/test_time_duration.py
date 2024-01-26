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
"""Tests for the module time."""

from operator import eq
from operator import ge
from operator import gt
from operator import le
from operator import lt

import pytest

from gemseo_fmu.utils.time_duration import TimeDuration


@pytest.mark.parametrize(
    ("value", "expected_value_in_seconds"),
    [(70.6, 70.6), ("70.6s", 70.6), ("1d 23m 2ms", 87780.002)],
)
def test_numbers_and_strings(value, expected_value_in_seconds):
    """Verify that Time accepts both numerical and string values."""
    assert TimeDuration(value).value == expected_value_in_seconds


@pytest.mark.parametrize(
    ("value", "other_value", "operators"),
    [(1, 1, (eq, le, ge)), (1, 2, (lt, le)), (2, 1, (gt, ge))],
)
def test_comparison(value, other_value, operators):
    """Verify that Time instances can be compared."""
    for operator in operators:
        assert operator(TimeDuration(value), TimeDuration(other_value))


@pytest.mark.parametrize(
    ("value", "name", "expected"),
    [
        (1.6, "microseconds", 1600000),
        (1.6, "milliseconds", 1600),
        (1.6, "seconds", 1.6),
        (4500, "minutes", 75),
        (4500, "hours", 1.25),
        (108000, "days", 1.25),
        (907200, "weeks", 1.5),
        (47336400, "months", 18),
        (47336400, "years", 1.5),
    ],
)
def test_units(value, name, expected):
    """Verify that Time can be expressed with usual time units."""
    time = TimeDuration(value)
    assert getattr(time, name) == expected
