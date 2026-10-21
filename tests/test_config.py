"""Тесты проверки настроек приложения."""

import os
import unittest
from unittest.mock import patch

from yaotel.config import Settings


class SettingsTests(unittest.TestCase):
    def test_starttls_defaults_to_enabled(self) -> None:
        with patch("yaotel.config.dotenv_values", return_value={}), patch.dict(
            os.environ, {}, clear=True
        ):
            self.assertTrue(Settings.from_env().smtp_starttls)

    def test_invalid_starttls_value_is_rejected(self) -> None:
        with patch("yaotel.config.dotenv_values", return_value={}), patch.dict(
            os.environ, {"YAOTEL_SMTP_STARTTLS": "treu"}, clear=True
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
