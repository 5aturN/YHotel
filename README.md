# ЯОтель

ЯОтель предоставляет HTTP API для поиска гостиничных номеров и управления бронированиями. Гости регистрируются, входят по электронной почте и паролю, создают брони и отменяют собственные брони. Сервис проверяет вместимость, состояние номера и пересечение дат, а сумму рассчитывает в копейках.

## Быстрый запуск

Требуются Python 3.11+ и pip.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

В `.env` замените значения `YAOTEL_API_KEY` и `YAOTEL_AUTH_SECRET` случайными строками длиной не менее 32 байт. Затем запустите приложение:

```powershell
python -m uvicorn yaotel.main:app --app-dir src --reload
```

Проверка доступности: `http://127.0.0.1:8000/health`. Интерактивная документация API: `http://127.0.0.1:8000/docs`.

## Возможности

- Поиск номеров по датам заезда и выезда, числу гостей и доступности.
- Регистрация гостей и выдача ограниченных по времени bearer-токенов.
- Создание, просмотр и отмена собственных бронирований.
- Интеграционный поиск номеров, защищенный API-ключом.
- Опциональные подтверждения бронирования по SMTP.

Руководство гостя находится в [docs/user-guide.md](docs/user-guide.md), описание маршрутов — в [docs/api.md](docs/api.md), устройство сервиса — в [docs/architecture.md](docs/architecture.md).

## Проверка и контейнер

```powershell
python -m pytest -q
python -m unittest discover -s tests -v
python -m ruff check src tests
docker build -t yaotel:dev .
docker run --rm -p 8000:8000 yaotel:dev
```

Настройки приложения и SMTP описаны в [docs/development.md](docs/development.md). Не добавляйте `.env`, настоящие учетные данные, ключи или данные гостей в систему контроля версий.
