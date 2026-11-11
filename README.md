# gauge-time-series-tools

Stores timestamped gauge readings and answers windowed queries: the last value at or before a timestamp, and the average value over a half-open interval.

```python
from gauge_time_series_tools import GaugeSeries, Reading

series = GaugeSeries()
series.add(1, 10.0)
series.add(2, 20.0)
series.add(3, 30.0)

last = series.last_value_before(2.5)
assert last == Reading(2, 20.0)

avg = series.average_over(1, 3)  # [1, 3)
assert avg is not None and abs(avg - 15.0) < 1e-9
```

## Why this exists

Gauge telemetry arrives as a stream of timestamped samples, but consumers often need aggregate state at a specific moment: what was the last known value, or what was the average over a window. Storing the raw stream and scanning it for every query is straightforward but slow for long series. This library keeps readings in chronological order and uses binary search for both queries.

The trade-off is strict ordering: `GaugeSeries.add` rejects a timestamp earlier than the last stored one. That keeps queries simple and fast, but it means callers must feed data in chronological order. If your source can produce out-of-order samples, sort them before adding.

## Edge case to know

`average_over(start, end)` uses a half-open interval `[start, end)`. A reading exactly at `end` is excluded, while a reading exactly at `start` is included. This avoids double-counting when adjacent windows are queried. If you want an inclusive right boundary, query `average_over(start, end + smallest_step)` or filter the result yourself.

## API

- `Reading(timestamp, value)` — immutable pair.
- `GaugeSeries(readings=None)` — ordered container. Methods: `add(timestamp, value)`, `readings()`, `last_value_before(timestamp)`, `average_over(start, end)`, `__len__`, `__iter__`.
- `last_value_before(series, timestamp)` and `average_over(series, start, end)` — module-level convenience wrappers.
