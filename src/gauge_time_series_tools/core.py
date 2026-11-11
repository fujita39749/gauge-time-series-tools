"""Core implementation for gauge time series storage and windowed queries.

The library stores readings as (timestamp, value) pairs and supports two
queries that are common when reconstructing aggregate state from periodic
gauge samples:

* ``last_value_before``: the most recent reading at or before a timestamp.
* ``average_over``: the arithmetic mean of readings in a half-open interval.

Timestamps are numeric (int or float) and must be monotonically non-decreasing
when inserted. Values are numeric. This keeps the implementation simple and
predictable: no timezone handling, no implicit ordering of arbitrary data.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class Reading:
    """A single timestamped gauge reading.

    Attributes:
        timestamp: Numeric time coordinate. Must be comparable with other
            timestamps in the same series.
        value: Numeric gauge value.
    """

    timestamp: float
    value: float


class GaugeSeries:
    """A time-ordered collection of gauge readings.

    Readings are kept sorted by timestamp. Inserting a reading with a timestamp
    earlier than the current maximum is rejected with ``ValueError`` because
    allowing out-of-order insertion would silently invalidate the binary-search
    based window queries. The trade-off is that callers must feed data in
    chronological order, which is the normal case for gauge telemetry.
    """

    def __init__(self, readings: Optional[Iterable[Reading]] = None) -> None:
        self._timestamps: List[float] = []
        self._values: List[float] = []
        if readings is not None:
            for reading in readings:
                self.add(reading.timestamp, reading.value)

    def add(self, timestamp: float, value: float) -> None:
        """Append a reading.

        Raises:
            ValueError: If ``timestamp`` is less than the last stored timestamp.
        """
        if self._timestamps and timestamp < self._timestamps[-1]:
            raise ValueError(
                f"timestamp {timestamp!r} is earlier than the last stored "
                f"timestamp {self._timestamps[-1]!r}"
            )
        self._timestamps.append(timestamp)
        self._values.append(value)

    def __len__(self) -> int:
        return len(self._timestamps)

    def __iter__(self):
        """Iterate over readings in timestamp order."""
        for ts, value in zip(self._timestamps, self._values):
            yield Reading(ts, value)

    def readings(self) -> List[Reading]:
        """Return a copy of all readings in timestamp order."""
        return [Reading(ts, value) for ts, value in zip(self._timestamps, self._values)]

    def last_value_before(self, timestamp: float) -> Optional[Reading]:
        """Return the latest reading with timestamp <= ``timestamp``.

        This is the state you would reconstruct at ``timestamp`` from the most
        recent sample at or before it. Returns ``None`` when no reading exists
        at or before ``timestamp``.
        """
        index = bisect_right(self._timestamps, timestamp) - 1
        if index < 0:
            return None
        return Reading(self._timestamps[index], self._values[index])

    def average_over(self, start: float, end: float) -> Optional[float]:
        """Return the mean value of readings in the half-open interval [start, end).

        The half-open interval avoids double counting readings that sit exactly
        on a boundary when adjacent windows are queried. Returns ``None`` when
        the interval contains no readings.

        Raises:
            ValueError: If ``end`` is less than ``start``.
        """
        if end < start:
            raise ValueError(f"end {end!r} is less than start {start!r}")
        left = bisect_left(self._timestamps, start)
        # bisect_left gives the first index at or after ``end``, so the right
        # boundary is exclusive.
        right = bisect_left(self._timestamps, end)
        if left >= right:
            return None
        total = 0.0
        for value in self._values[left:right]:
            total += value
        return total / (right - left)


def last_value_before(series: GaugeSeries, timestamp: float) -> Optional[Reading]:
    """Convenience wrapper around :meth:`GaugeSeries.last_value_before`."""
    return series.last_value_before(timestamp)


def average_over(series: GaugeSeries, start: float, end: float) -> Optional[float]:
    """Convenience wrapper around :meth:`GaugeSeries.average_over`."""
    return series.average_over(start, end)
