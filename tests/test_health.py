"""Проверки работоспособности приложения."""

import unittest

from fastapi.testclient import TestClient

from yaotel.api import create_app
from yaotel.config import Settings


class HealthEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(Settings(database_url="sqlite+pysqlite:///:memory:"))

    def tearDown(self) -> None:
        self.app.state.engine.dispose()

    def test_health_returns_ok(self) -> None:
        with TestClient(self.app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
