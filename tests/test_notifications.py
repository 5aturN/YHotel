"""Интеграционные тесты SMTP-уведомлений с локальным сервером приема."""

import socket
import unittest
from email import policy
from email.parser import BytesParser

from aiosmtpd.controller import Controller

from yaotel.config import Settings
from yaotel.notifications import send_booking_confirmation


class MessageCollector:
    def __init__(self) -> None:
        self.messages: list[bytes] = []

    async def handle_DATA(self, _server, _session, envelope):
        self.messages.append(envelope.content)
        return "250 Message accepted for delivery"


class NotificationTests(unittest.TestCase):
    def test_booking_confirmation_is_delivered_to_local_smtp_server(self) -> None:
        collector = MessageCollector()
        with socket.socket() as reserved_port:
            reserved_port.bind(("127.0.0.1", 0))
            smtp_port = reserved_port.getsockname()[1]

        controller = Controller(collector, hostname="127.0.0.1", port=smtp_port)
        controller.start()
        try:
            settings = Settings(
                smtp_host="127.0.0.1",
                smtp_port=smtp_port,
                smtp_from_email="bookings@example.test",
                smtp_starttls=False,
            )
            send_booking_confirmation(
                settings,
                "guest@example.test",
                "booking-123",
                101,
                "2030-01-04",
                "2030-01-07",
                2,
                2_805_000,
            )
        finally:
            controller.stop()

        self.assertEqual(len(collector.messages), 1)
        message = BytesParser(policy=policy.default).parsebytes(collector.messages[0])
        self.assertEqual(message["To"], "guest@example.test")
        self.assertIn("booking-123", message["Subject"])
        self.assertIn("28050.00 RUB", message.get_content())


if __name__ == "__main__":
    unittest.main()
