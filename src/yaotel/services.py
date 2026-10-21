"""Сервисный слой операций бронирования."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from yaotel.models import Booking
from yaotel.pricing import PriceCalculator
from yaotel.repository import (
    booking_overlaps,
    get_booking,
    get_room_for_booking,
    list_available_rooms,
)


class BookingConflict(Exception):
    """Возникает, когда номер недоступен в выбранный период."""


class RoomNotFound(Exception):
    """Возникает, когда выбранный номер не существует."""


class BookingNotFound(Exception):
    """Возникает, когда бронирование не существует."""


class BookingNotOwned(Exception):
    """Возникает при попытке получить доступ к чужому бронированию."""


class BookingStateConflict(Exception):
    """Возникает, когда бронирование нельзя отменить в текущем состоянии."""


class BookingService:
    """Координирует поиск номеров, расчет стоимости и сохранение бронирования."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def available_rooms(
        self, check_in: date, check_out: date, guests: int
    ):
        if check_out <= check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда.")
        if guests < 1:
            raise ValueError("Укажите хотя бы одного гостя.")
        return list_available_rooms(self.session, check_in, check_out, guests)

    def create_booking(
        self,
        *,
        user_id: int,
        room_id: int,
        check_in: date,
        check_out: date,
        guests: int,
    ) -> Booking:
        if check_out <= check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда.")
        if guests < 1:
            raise ValueError("Укажите хотя бы одного гостя.")

        try:
            room = get_room_for_booking(self.session, room_id)
            if room is None:
                raise RoomNotFound
            if room.status not in {"clean", "inspected"} or room.capacity < guests:
                raise BookingConflict
            if booking_overlaps(self.session, room_id, check_in, check_out):
                raise BookingConflict

            booking = Booking(
                id=str(uuid.uuid4()),
                room_id=room.id,
                user_id=user_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                total_price_kopecks=PriceCalculator.calculate_total_kopecks(
                    room.base_price_kopecks, check_in, check_out
                ),
                status="pending",
            )
            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)
            return booking
        except Exception:
            self.session.rollback()
            raise

    def get_user_booking(self, booking_id: str, user_id: int) -> Booking:
        booking = get_booking(self.session, booking_id)
        if booking is None:
            raise BookingNotFound
        if booking.user_id != user_id:
            raise BookingNotOwned
        return booking

    def cancel_booking(self, booking_id: str, user_id: int) -> None:
        booking = self.get_user_booking(booking_id, user_id)
        if booking.status in {"checked_in", "checked_out", "cancelled"}:
            raise BookingStateConflict
        booking.status = "cancelled"
        self.session.commit()
