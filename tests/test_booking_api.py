"""Integration tests for the initial room booking API."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from yaotel.api import create_app
from yaotel.config import Settings


class BookingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            Settings(
                database_url="sqlite+pysqlite:///:memory:",
                api_key="test-api-key",
                auth_secret="test-only-signing-secret-with-32-bytes",
            )
        )
        self.client = TestClient(self.app)
        self.headers = self.create_account("guest@example.com")

    def tearDown(self) -> None:
        self.client.close()
        self.app.state.engine.dispose()

    def create_account(self, email: str) -> dict[str, str]:
        payload = {"email": email, "password": "correct-horse-battery-staple"}
        registered = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(registered.status_code, 201)
        logged_in = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(logged_in.status_code, 200)
        return {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

    def test_integration_api_requires_key(self) -> None:
        response = self.client.get(
            "/api/integrations/rooms/availability",
            params={"check_in": "2030-01-04", "check_out": "2030-01-07", "guests": 2},
        )
        self.assertEqual(response.status_code, 401)

    def test_booking_creation_blocks_overlapping_dates(self) -> None:
        payload = {
            "room_id": 1,
            "check_in": "2030-01-04",
            "check_out": "2030-01-07",
            "guests": 2,
        }
        with patch("yaotel.api.send_booking_confirmation") as send_confirmation:
            response = self.client.post("/api/bookings", json=payload, headers=self.headers)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "pending")
            self.assertEqual(response.json()["total_price_kopecks"], 2_805_000)
            self.assertNotIn("guest_email", response.json())

            conflict = self.client.post("/api/bookings", json=payload, headers=self.headers)
            send_confirmation.assert_called_once()
        self.assertEqual(conflict.status_code, 409)

    def test_invalid_stay_is_rejected(self) -> None:
        response = self.client.get(
            "/api/rooms/availability",
            params={"check_in": "2030-01-07", "check_out": "2030-01-04", "guests": 2},
        )
        self.assertEqual(response.status_code, 422)

    def test_booking_requires_authentication(self) -> None:
        response = self.client.post(
            "/api/bookings",
            json={
                "room_id": 1,
                "check_in": "2030-01-04",
                "check_out": "2030-01-07",
                "guests": 2,
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_guests_cannot_read_or_cancel_another_guests_booking(self) -> None:
        payload = {
            "room_id": 1,
            "check_in": "2030-01-04",
            "check_out": "2030-01-07",
            "guests": 2,
        }
        created = self.client.post("/api/bookings", json=payload, headers=self.headers)
        booking_id = created.json()["id"]
        other_headers = self.create_account("other@example.com")

        read_response = self.client.get(f"/api/bookings/{booking_id}", headers=other_headers)
        cancel_response = self.client.delete(f"/api/bookings/{booking_id}", headers=other_headers)
        listed_response = self.client.get("/api/bookings", headers=other_headers)

        self.assertEqual(read_response.status_code, 403)
        self.assertEqual(cancel_response.status_code, 403)
        self.assertEqual(listed_response.json(), [])

    def test_owner_can_cancel_booking_without_deleting_history(self) -> None:
        payload = {
            "room_id": 1,
            "check_in": "2030-01-04",
            "check_out": "2030-01-07",
            "guests": 2,
        }
        created = self.client.post("/api/bookings", json=payload, headers=self.headers)
        booking_id = created.json()["id"]

        cancelled = self.client.delete(f"/api/bookings/{booking_id}", headers=self.headers)
        details = self.client.get(f"/api/bookings/{booking_id}", headers=self.headers)
        replacement = self.client.post("/api/bookings", json=payload, headers=self.headers)

        self.assertEqual(cancelled.status_code, 204)
        self.assertEqual(details.json()["status"], "cancelled")
        self.assertEqual(replacement.status_code, 201)

    def test_integration_key_and_public_search_return_room_data(self) -> None:
        params = {"check_in": "2030-01-04", "check_out": "2030-01-07", "guests": 2}
        public_response = self.client.get("/api/rooms/availability", params=params)
        integration_response = self.client.get(
            "/api/integrations/rooms/availability",
            params=params,
            headers={"X-API-Key": "test-api-key"},
        )

        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(integration_response.status_code, 200)
        self.assertEqual(public_response.json(), integration_response.json())


if __name__ == "__main__":
    unittest.main()
