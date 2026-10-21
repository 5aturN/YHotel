# Разработка и настройка

## Переменные окружения

Скопируйте `.env.example` в `.env` и замените демонстрационные значения.

| Переменная | Назначение |
|---|---|
| `YAOTEL_DATABASE_URL` | SQLAlchemy URL; по умолчанию локальная SQLite |
| `YAOTEL_AUTH_SECRET` | Секрет подписи bearer-токенов, минимум 32 случайных байта |
| `YAOTEL_ACCESS_TOKEN_MINUTES` | Срок жизни токена в минутах |
| `YAOTEL_API_KEY` | Ключ интеграционного маршрута поиска номеров |
| `YAOTEL_SMTP_HOST` / `YAOTEL_SMTP_PORT` | Сервер отправки почты |
| `YAOTEL_SMTP_USERNAME` / `YAOTEL_SMTP_PASSWORD` | Необязательные учетные данные SMTP |
| `YAOTEL_FROM_EMAIL` | Адрес отправителя |
| `YAOTEL_SMTP_STARTTLS` | Использовать STARTTLS; включено по умолчанию |

SMTP включается только при заданных хосте и адресе отправителя. Сбой отправки журналируется и не отменяет уже сохраненную бронь. Пароли и токены не записываются в сообщения логов.

## Тесты и проверки

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check src tests
python -m bandit -r src/yaotel -ll
pip-audit -r requirements-dev.txt
```

SMTP проверяется локальным приемником сообщений; реальные почтовые учетные данные тестам не требуются. Workflow CI запускает проверки и собирает контейнер при изменениях `main`, `develop` и pull request.
