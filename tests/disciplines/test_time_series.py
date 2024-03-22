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
"""Test for time series."""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError

import pytest

from gemseo_fmu.disciplines.time_series import TimeSeries


def test_time_series():
    """Check the use of TimeSeries."""
    time_series = TimeSeries([1, 2], [3, 4])
    assert time_series.time == [1, 2]
    assert time_series.observable == [3, 4]
    assert time_series.size == 2


def test_frozen_time_series():
    """Check that the TimeSeries is a frozen dataclass."""
    time_series = TimeSeries([1, 2], [3, 4])
    with pytest.raises(
        FrozenInstanceError, match=re.escape("cannot assign to field 'time'")
    ):
        time_series.time = [5, 6]


def test_time_series_error():
    """Check the use of TimeSeries with time and observable of different lengths."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The lengths of fields 'time' (2) and 'observable' (3) do not match."
        ),
    ):
        TimeSeries([1, 2], [3, 4, 5])


def test_time_series_from_string_time_values():
    """Check that the TimeSeries can be set from string time values."""
    time_series = TimeSeries(["1h", "2h"], [3, 4])
    assert time_series.time == [3600, 7200]


@pytest.mark.parametrize(("time", "expected"), [(1, 3), (1.5, 3), (2, 4), (2.5, 4)])
def test_compute(time, expected):
    """Verify that TimeSeries.compute is a stairs function."""
    time_series = TimeSeries([1, 2], [3, 4])
    assert time_series.compute(time) == expected


def test_compute_string():
    """Verify that TimeSeries.compute works with string values."""
    time_series = TimeSeries([1, 2], [3, 4])
    assert time_series.compute("1.5s") == 3


def test_compute_error():
    """Verify that TimeSeries.compute cannot be evaluated before the first time."""
    time_series = TimeSeries([1, 2], [3, 4])
    with pytest.raises(
        ValueError, match=re.escape("The time series starts at 1; got 0.5.")
    ):
        time_series.compute(0.5)


@pytest.mark.parametrize(
    ("other_time_series", "are_equal"),
    [
        (TimeSeries([1, 2], [3, 4]), True),
        (TimeSeries([1, 2], [3, 5]), False),
        (TimeSeries([1, 3], [3, 4]), False),
        (TimeSeries([1, 3], [3, 5]), False),
        (1, False),
    ],
)
def test_eq(other_time_series, are_equal):
    """Verify that the __eq__ method works correctly."""
    assert (TimeSeries([1, 2], [3, 4]) == other_time_series) == are_equal
