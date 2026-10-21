"""Настройки приложения из переменных окружения или переданных параметров."""

import os
from dataclasses import dataclass

from dotenv import dotenv_values


def parse_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name}: значение должно быть логическим.")


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/yaotel.sqlite3"
    api_key: str | None = None
    auth_secret: str | None = None
    access_token_minutes: int = 30
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True
    smtp_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        values = {**dotenv_values(), **os.environ}
        return cls(
            database_url=values.get("YAOTEL_DATABASE_URL", cls.database_url),
            api_key=values.get("YAOTEL_API_KEY"),
            auth_secret=values.get("YAOTEL_AUTH_SECRET"),
            access_token_minutes=int(values.get("YAOTEL_ACCESS_TOKEN_MINUTES", "30")),
            smtp_host=values.get("YAOTEL_SMTP_HOST") or None,
            smtp_port=int(values.get("YAOTEL_SMTP_PORT", "587")),
            smtp_username=values.get("YAOTEL_SMTP_USERNAME") or None,
            smtp_password=values.get("YAOTEL_SMTP_PASSWORD") or None,
            smtp_from_email=values.get("YAOTEL_FROM_EMAIL") or None,
            smtp_starttls=parse_bool(
                "YAOTEL_SMTP_STARTTLS",
                values.get("YAOTEL_SMTP_STARTTLS", "true"),
            ),
        )
