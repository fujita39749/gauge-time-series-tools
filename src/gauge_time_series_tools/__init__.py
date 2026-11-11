"""Gauge time series tools: timestamped readings with windowed queries.

Exports:
    GaugeSeries: container for timestamped gauge readings.
    Reading: a single timestamped reading.
    last_value_before: return the most recent reading strictly before a timestamp.
    average_over: return the mean value of readings in a half-open interval.
"""

from .core import GaugeSeries, Reading, last_value_before, average_over

__all__ = [
    "GaugeSeries",
    "Reading",
    "last_value_before",
    "average_over",
]
