"""Доступ к данным номеров и бронирований."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from yaotel.models import Booking, Room, User

ACTIVE_BOOKING_STATUSES = ("pending", "confirmed", "checked_in")
READY_ROOM_STATUSES = ("clean", "inspected")


def list_available_rooms(
    session: Session, check_in: date, check_out: date, guests: int
) -> list[Room]:
    """Возвращает готовые номера нужной вместимости без пересекающихся бронирований."""
    overlapping_booking = (
        select(Booking.id)
        .where(
            Booking.room_id == Room.id,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        .exists()
    )
    statement = (
        select(Room)
        .where(
            Room.capacity >= guests,
            Room.status.in_(READY_ROOM_STATUSES),
            ~overlapping_booking,
        )
        .order_by(Room.number)
    )
    return list(session.scalars(statement))


def get_room_for_booking(session: Session, room_id: int) -> Room | None:
    """Блокирует выбранный номер на время проверки и создания бронирования."""
    return session.scalar(select(Room).where(Room.id == room_id).with_for_update())


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def get_booking(session: Session, booking_id: str) -> Booking | None:
    return session.get(Booking, booking_id)


def list_user_bookings(session: Session, user_id: int) -> list[Booking]:
    statement = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc(), Booking.id)
    )
    return list(session.scalars(statement))


def booking_overlaps(
    session: Session, room_id: int, check_in: date, check_out: date
) -> bool:
    statement = select(Booking.id).where(
        Booking.room_id == room_id,
        Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    )
    return session.scalar(statement.limit(1)) is not None
