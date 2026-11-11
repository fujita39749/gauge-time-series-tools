import math
import unittest

from gauge_time_series_tools import (
    GaugeSeries,
    Reading,
    average_over,
    last_value_before,
)


class TestGaugeSeries(unittest.TestCase):
    def test_empty_series(self):
        series = GaugeSeries()
        self.assertEqual(len(series), 0)
        self.assertEqual(series.readings(), [])
        self.assertIsNone(series.last_value_before(10))
        self.assertIsNone(series.average_over(0, 10))

    def test_add_and_iterate(self):
        series = GaugeSeries()
        series.add(1, 10.0)
        series.add(2, 20.0)
        series.add(3, 30.0)
        self.assertEqual(len(series), 3)
        self.assertEqual(
            list(series),
            [Reading(1, 10.0), Reading(2, 20.0), Reading(3, 30.0)],
        )

    def test_readings_returns_copy(self):
        series = GaugeSeries([Reading(1, 5.0)])
        copy = series.readings()
        copy.append(Reading(2, 6.0))
        self.assertEqual(len(series), 1)
        self.assertEqual(series.readings(), [Reading(1, 5.0)])

    def test_out_of_order_insertion_rejected(self):
        series = GaugeSeries()
        series.add(5, 1.0)
        with self.assertRaises(ValueError):
            series.add(4, 2.0)
        self.assertEqual(len(series), 1)

    def test_equal_timestamps_allowed(self):
        series = GaugeSeries()
        series.add(5, 1.0)
        series.add(5, 2.0)
        self.assertEqual(len(series), 2)
        self.assertEqual(series.last_value_before(5), Reading(5, 2.0))

    def test_last_value_before_exact_and_between(self):
        series = GaugeSeries([Reading(1, 10.0), Reading(3, 30.0), Reading(5, 50.0)])
        self.assertEqual(series.last_value_before(3), Reading(3, 30.0))
        self.assertEqual(series.last_value_before(4), Reading(3, 30.0))
        self.assertEqual(series.last_value_before(5), Reading(5, 50.0))
        self.assertEqual(series.last_value_before(1), Reading(1, 10.0))

    def test_last_value_before_returns_none_too_early(self):
        series = GaugeSeries([Reading(2, 20.0)])
        self.assertIsNone(series.last_value_before(1))

    def test_average_over_half_open_interval(self):
        series = GaugeSeries([Reading(1, 10.0), Reading(2, 20.0), Reading(3, 30.0)])
        # [1, 3) includes timestamps 1 and 2, not 3.
        got = series.average_over(1, 3)
        self.assertIsNotNone(got)
        self.assertTrue(math.isclose(got, 15.0, rel_tol=1e-9))

    def test_average_over_excludes_end_boundary(self):
        series = GaugeSeries([Reading(1, 10.0), Reading(2, 20.0), Reading(3, 30.0)])
        got = series.average_over(1, 2)
        self.assertIsNotNone(got)
        self.assertTrue(math.isclose(got, 10.0, rel_tol=1e-9))

    def test_average_over_empty_interval(self):
        series = GaugeSeries([Reading(1, 10.0), Reading(3, 30.0)])
        self.assertIsNone(series.average_over(1.5, 2.5))

    def test_average_over_reversed_bounds(self):
        series = GaugeSeries([Reading(1, 10.0)])
        with self.assertRaises(ValueError):
            series.average_over(5, 1)

    def test_average_over_zero_length_interval(self):
        series = GaugeSeries([Reading(1, 10.0), Reading(2, 20.0)])
        self.assertIsNone(series.average_over(2, 2))

    def test_module_level_wrappers(self):
        series = GaugeSeries([Reading(1, 4.0), Reading(2, 8.0)])
        self.assertEqual(last_value_before(series, 2), Reading(2, 8.0))
        got = average_over(series, 1, 2)
        self.assertIsNotNone(got)
        self.assertTrue(math.isclose(got, 4.0, rel_tol=1e-9))


if __name__ == "__main__":
    unittest.main()
