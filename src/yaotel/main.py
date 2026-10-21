"""Точка входа ASGI; обработчики маршрутов находятся в модуле API."""

from yaotel.api import create_app

app = create_app()
