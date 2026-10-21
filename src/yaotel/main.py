"""ASGI entry point; route logic lives in the API module."""

from yaotel.api import create_app

app = create_app()
