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
"""TimeManager."""

import logging
import re

import pytest

from gemseo_fmu.utils.time_manager import TimeManager


@pytest.fixture
def time_manager() -> TimeManager:
    """A time manager."""
    return TimeManager(1.2, 4.5, 2.3)


def test_properties(time_manager):
    """Check properties."""
    assert time_manager.initial == 1.2
    assert time_manager.current == 1.2
    assert time_manager.final == 4.5
    assert time_manager.remaining == 3.3


def test_time_manager(time_manager, caplog):
    """Check update_current_time()."""
    caplog.set_level(logging.DEBUG, "gemseo_fmu.utils.time_manager")
    times = time_manager.update_current_time()
    assert times == TimeManager(1.2, 3.5, 2.3)
    assert time_manager.initial == 1.2
    assert time_manager.current == 3.5
    assert time_manager.final == 4.5
    assert time_manager.remaining == 1.0
    times = time_manager.update_current_time()
    assert times == TimeManager(3.5, 4.5, 1.0)
    assert time_manager.initial == 1.2
    assert time_manager.current == 4.5
    assert time_manager.final == 4.5
    assert (
        "gemseo_fmu.utils.time_manager",
        logging.DEBUG,
        (
            "The time step is greater than the remaining time; "
            "use the remaining time instead."
        ),
    ) in caplog.record_tuples
    assert time_manager.remaining == 0.0
    with pytest.raises(
        ValueError,
        match=re.escape(
            "The current time cannot be incremented as it is the final time (4.5)."
        ),
    ):
        time_manager.update_current_time()


def test_time_manager_custom(time_manager):
    """Check update_current_time() with custom values."""
    update_current_time = time_manager.update_current_time
    assert update_current_time(0.5) == TimeManager(1.2, 1.7, 0.5)
    assert update_current_time(return_time_manager=False) == (1.7, 4.0, 2.3)


@pytest.mark.parametrize(
    ("other_time_manager", "expected"),
    [
        (1, False),
        (TimeManager(1.2, 4.5, 2.3), True),
        (TimeManager(-1.2, 4.5, 2.3), False),
        (TimeManager(1.2, -4.5, 2.3), False),
        (TimeManager(1.2, 4.5, -2.3), False),
    ],
)
def test_eq(time_manager, other_time_manager, expected):
    """Check __eq__()."""
    assert (time_manager == other_time_manager) is expected


def test_reset(time_manager):
    """Check reset()."""
    time_manager.update_current_time()
    time_manager.reset()
    assert time_manager.initial == 1.2
    assert time_manager.current == 1.2
    assert time_manager.final == 4.5
    assert time_manager.remaining == 3.3
