"""Application services for booking operations."""

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
    """Raised when a room is not available for the requested interval."""


class RoomNotFound(Exception):
    """Raised when the requested room does not exist."""


class BookingNotFound(Exception):
    """Raised when the requested booking does not exist."""


class BookingNotOwned(Exception):
    """Raised when a user attempts to access another user's booking."""


class BookingStateConflict(Exception):
    """Raised when a booking cannot be cancelled in its current state."""


class BookingService:
    """Coordinate room availability, price calculation, and booking persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def available_rooms(
        self, check_in: date, check_out: date, guests: int
    ):
        if check_out <= check_in:
            raise ValueError("Check-out date must be later than check-in date.")
        if guests < 1:
            raise ValueError("At least one guest is required.")
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
            raise ValueError("Check-out date must be later than check-in date.")
        if guests < 1:
            raise ValueError("At least one guest is required.")

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
