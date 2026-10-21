"""Правила расчета стоимости проживания по ночам."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal


class PriceCalculator:
    """Рассчитывает стоимость проживания в копейках без ошибок округления."""

    WEEKEND_MULTIPLIER = Decimal("1.15")
    WEEKEND_NIGHT_STARTS = frozenset({4, 5})  # Friday and Saturday nights

    @classmethod
    def calculate_total_kopecks(
        cls, base_price_kopecks: int, check_in: date, check_out: date
    ) -> int:
        """Рассчитывает сумму за интервал [заезд, выезд), учитывая каждую ночь один раз."""
        if base_price_kopecks <= 0:
            raise ValueError("Base price must be a positive number of kopecks.")
        if check_out <= check_in:
            raise ValueError("Check-out date must be later than check-in date.")

        total = Decimal(0)
        night = check_in
        while night < check_out:
            multiplier = (
                cls.WEEKEND_MULTIPLIER
                if night.weekday() in cls.WEEKEND_NIGHT_STARTS
                else Decimal(1)
            )
            total += Decimal(base_price_kopecks) * multiplier
            night += timedelta(days=1)
        return int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
