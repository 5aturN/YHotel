"""Unit tests for the core nightly-price calculation."""

import unittest
from datetime import date

from yaotel.pricing import PriceCalculator


class PriceCalculatorTests(unittest.TestCase):
    def test_weekday_nights_use_base_rate(self) -> None:
        total = PriceCalculator.calculate_total_kopecks(10_000, date(2030, 1, 7), date(2030, 1, 9))
        self.assertEqual(total, 20_000)

    def test_friday_and_saturday_nights_use_weekend_rate(self) -> None:
        total = PriceCalculator.calculate_total_kopecks(10_000, date(2030, 1, 4), date(2030, 1, 7))
        self.assertEqual(total, 33_000)

    def test_checkout_is_exclusive(self) -> None:
        total = PriceCalculator.calculate_total_kopecks(10_000, date(2030, 1, 4), date(2030, 1, 5))
        self.assertEqual(total, 11_500)

    def test_rejects_empty_or_reversed_stay(self) -> None:
        with self.assertRaises(ValueError):
            PriceCalculator.calculate_total_kopecks(10_000, date(2030, 1, 5), date(2030, 1, 5))
        with self.assertRaises(ValueError):
            PriceCalculator.calculate_total_kopecks(10_000, date(2030, 1, 6), date(2030, 1, 5))

    def test_rejects_non_positive_rate(self) -> None:
        with self.assertRaises(ValueError):
            PriceCalculator.calculate_total_kopecks(0, date(2030, 1, 4), date(2030, 1, 5))

    def test_rounds_to_a_whole_kopeck(self) -> None:
        total = PriceCalculator.calculate_total_kopecks(10, date(2030, 1, 4), date(2030, 1, 5))
        self.assertEqual(total, 12)


if __name__ == "__main__":
    unittest.main()
