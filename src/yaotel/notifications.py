"""SMTP delivery for booking confirmations."""

import logging
import smtplib
import ssl
from decimal import Decimal
from email.message import EmailMessage

from yaotel.config import Settings

logger = logging.getLogger(__name__)


def send_booking_confirmation(
    settings: Settings,
    recipient: str,
    booking_id: str,
    room_id: int,
    check_in: str,
    check_out: str,
    guests: int,
    total_price_kopecks: int,
) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        logger.info("SMTP notifications are not configured.")
        return
    if bool(settings.smtp_username) != bool(settings.smtp_password):
        logger.warning("SMTP delivery is disabled because credentials are incomplete.")
        return

    message = EmailMessage()
    message["Subject"] = f"Подтверждение бронирования {booking_id}"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    total_price = Decimal(total_price_kopecks) / 100
    message.set_content(
        "Бронирование создано.\n"
        f"Номер: {room_id}\n"
        f"Заезд: {check_in}\n"
        f"Выезд: {check_out}\n"
        f"Гостей: {guests}\n"
        f"Стоимость: {total_price:.2f} RUB\n"
        f"Номер бронирования: {booking_id}\n"
    )

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as client:
            client.ehlo()
            if settings.smtp_starttls:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.warning("Booking confirmation email could not be delivered.")
