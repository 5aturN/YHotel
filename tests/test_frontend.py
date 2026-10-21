"""Проверки пользовательской страницы бронирования."""

import unittest

from fastapi.testclient import TestClient

from yaotel.api import create_app
from yaotel.config import Settings


class CustomerPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(Settings(database_url="sqlite+pysqlite:///:memory:"))
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.state.engine.dispose()

    def test_homepage_serves_customer_booking_page(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Найдите номер для поездки", response.text)
        self.assertIn("/static/app.js", response.text)

    def test_static_assets_are_available(self) -> None:
        stylesheet = self.client.get("/static/styles.css")
        script = self.client.get("/static/app.js")
        room_images = [
            self.client.get(f"/static/rooms/{category}.png")
            for category in ("standard", "deluxe", "family", "suite")
        ]

        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn(".room-card", stylesheet.text)
        self.assertEqual(script.status_code, 200)
        self.assertIn("/api/rooms/availability", script.text)
        for category_name in ("Стандарт", "Делюкс", "Семейный", "Люкс"):
            self.assertIn(category_name, script.text)
        for room_image in room_images:
            self.assertEqual(room_image.status_code, 200)
            self.assertEqual(room_image.headers["content-type"], "image/png")
            self.assertTrue(room_image.content.startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
