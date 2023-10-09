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
