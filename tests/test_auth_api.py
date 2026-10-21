"""Account registration and login API tests."""

import unittest

from fastapi.testclient import TestClient
from sqlalchemy import select

from yaotel.api import create_app
from yaotel.config import Settings
from yaotel.models import User


class AuthenticationApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            Settings(
                database_url="sqlite+pysqlite:///:memory:",
                auth_secret="test-only-signing-secret-with-32-bytes",
            )
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.state.engine.dispose()

    def test_registration_normalizes_email_and_stores_only_password_hash(self) -> None:
        payload = {"email": " Guest@Example.com ", "password": "correct-horse-battery-staple"}
        response = self.client.post("/api/auth/register", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "guest@example.com")
        self.assertNotIn("password", response.json())
        self.assertNotIn("password_hash", response.json())
        with self.app.state.session_factory() as session:
            user = session.scalar(select(User).where(User.email == "guest@example.com"))
        self.assertIsNotNone(user)
        self.assertTrue(user.password_hash.startswith("$argon2id$"))
        self.assertNotEqual(user.password_hash, payload["password"])

    def test_duplicate_email_is_rejected_case_insensitively(self) -> None:
        payload = {"email": "guest@example.com", "password": "correct-horse-battery-staple"}
        first = self.client.post("/api/auth/register", json=payload)
        duplicate = self.client.post(
            "/api/auth/register",
            json={"email": "GUEST@example.com", "password": payload["password"]},
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 409)

    def test_login_returns_bearer_token_and_rejects_incorrect_password(self) -> None:
        payload = {"email": "guest@example.com", "password": "correct-horse-battery-staple"}
        self.client.post("/api/auth/register", json=payload)

        invalid = self.client.post(
            "/api/auth/login",
            json={"email": payload["email"], "password": "wrong-password"},
        )
        valid = self.client.post("/api/auth/login", json=payload)
        bookings = self.client.get(
            "/api/bookings",
            headers={"Authorization": f"Bearer {valid.json()['access_token']}"},
        )

        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.json()["token_type"], "bearer")
        self.assertEqual(bookings.status_code, 200)

    def test_short_password_is_rejected(self) -> None:
        response = self.client.post(
            "/api/auth/register",
            json={"email": "guest@example.com", "password": "short"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
