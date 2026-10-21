"""HTTP-маршруты для поиска номеров, аккаунтов и бронирований."""

import hmac
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yaotel.auth import create_access_token, get_token_user_id, hash_password, verify_password
from yaotel.config import Settings
from yaotel.db import create_database
from yaotel.models import User
from yaotel.notifications import send_booking_confirmation
from yaotel.repository import get_user_by_email, list_user_bookings
from yaotel.schemas import (
    BookingCreate,
    BookingRead,
    LoginRequest,
    RoomRead,
    TokenResponse,
    UserCreate,
    UserRead,
)
from yaotel.services import (
    BookingConflict,
    BookingNotFound,
    BookingNotOwned,
    BookingService,
    BookingStateConflict,
    RoomNotFound,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Создает приложение с заданными настройками и подключением к базе данных."""
    runtime_settings = settings or Settings.from_env()
    engine, session_factory = create_database(runtime_settings.database_url)
    app = FastAPI(
        title="ЯОтель API",
        version="0.2.0",
        description="API гостиничного сервиса для поиска номеров и управления бронированиями.",
    )
    app.state.settings = runtime_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    static_dir = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    bearer_scheme = HTTPBearer(auto_error=False)

    def get_session(request: Request):
        session: Session = request.app.state.session_factory()
        try:
            yield session
        finally:
            session.close()

    DbSession = Annotated[Session, Depends(get_session)]

    @app.get("/", include_in_schema=False)
    def customer_page() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    def get_auth_secret() -> str:
        secret = runtime_settings.auth_secret
        if not secret or len(secret.encode("utf-8")) < 32:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User authentication is not configured.",
            )
        if runtime_settings.access_token_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Access token lifetime is not configured.",
            )
        return secret

    def require_api_key(
        request: Request,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    ) -> None:
        expected = request.app.state.settings.api_key
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API access is not configured.",
            )
        if not x_api_key or not hmac.compare_digest(x_api_key, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid API key.",
            )

    def get_current_user(
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
        ],
        session: DbSession,
    ) -> User:
        secret = get_auth_secret()
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A bearer access token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = get_token_user_id(credentials.credentials, secret)
        user = session.get(User, user_id) if user_id is not None else None
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The access token is invalid or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @app.get("/health", tags=["Состояние сервиса"], summary="Проверить состояние сервиса")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/api/auth/register",
        response_model=UserRead,
        status_code=status.HTTP_201_CREATED,
        tags=["Учетная запись"],
        summary="Создать аккаунт гостя",
    )
    def register_user(request: UserCreate, session: DbSession) -> UserRead:
        get_auth_secret()
        user = User(email=request.email, password_hash=hash_password(request.password))
        session.add(user)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc
        session.refresh(user)
        return UserRead.model_validate(user)

    @app.post(
        "/api/auth/login",
        response_model=TokenResponse,
        tags=["Учетная запись"],
        summary="Получить токен доступа по учетным данным",
    )
    def login_user(request: LoginRequest, session: DbSession) -> TokenResponse:
        secret = get_auth_secret()
        user = get_user_by_email(session, request.email)
        if user is None or not user.is_active or not verify_password(
            request.password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenResponse(
            access_token=create_access_token(
                user.id, secret, runtime_settings.access_token_minutes
            ),
            expires_in=runtime_settings.access_token_minutes * 60,
        )

    def search_rooms(
        session: Session, check_in: date, check_out: date, guests: int
    ) -> list[RoomRead]:
        try:
            rooms = BookingService(session).available_rooms(check_in, check_out, guests)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return [RoomRead.model_validate(room) for room in rooms]

    @app.get(
        "/api/rooms/availability",
        response_model=list[RoomRead],
        tags=["Номера"],
        summary="Найти свободные номера на выбранные даты",
    )
    def room_availability(
        check_in: Annotated[date, Query()],
        check_out: Annotated[date, Query()],
        guests: Annotated[int, Query(ge=1, le=10)],
        session: DbSession,
    ) -> list[RoomRead]:
        return search_rooms(session, check_in, check_out, guests)

    @app.get(
        "/api/integrations/rooms/availability",
        response_model=list[RoomRead],
        dependencies=[Depends(require_api_key)],
        tags=["Интеграции"],
        summary="Найти свободные номера для авторизованной интеграции",
    )
    def integration_room_availability(
        check_in: Annotated[date, Query()],
        check_out: Annotated[date, Query()],
        guests: Annotated[int, Query(ge=1, le=10)],
        session: DbSession,
    ) -> list[RoomRead]:
        return search_rooms(session, check_in, check_out, guests)

    @app.post(
        "/api/bookings",
        response_model=BookingRead,
        status_code=status.HTTP_201_CREATED,
        tags=["Бронирования"],
        summary="Создать бронирование для вошедшего гостя",
    )
    def create_booking(
        request: BookingCreate,
        background_tasks: BackgroundTasks,
        session: DbSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> BookingRead:
        try:
            booking = BookingService(session).create_booking(
                user_id=current_user.id,
                room_id=request.room_id,
                check_in=request.check_in,
                check_out=request.check_out,
                guests=request.guests,
            )
        except RoomNotFound as exc:
            raise HTTPException(status_code=404, detail="Room not found.") from exc
        except BookingConflict as exc:
            raise HTTPException(
                status_code=409, detail="Room is not available for these dates."
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        background_tasks.add_task(
            send_booking_confirmation,
            runtime_settings,
            current_user.email,
            booking.id,
            booking.room_id,
            booking.check_in.isoformat(),
            booking.check_out.isoformat(),
            booking.guests,
            booking.total_price_kopecks,
        )
        return BookingRead.model_validate(booking)

    @app.get(
        "/api/bookings",
        response_model=list[BookingRead],
        tags=["Бронирования"],
        summary="Получить список бронирований гостя",
    )
    def get_bookings(
        session: DbSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> list[BookingRead]:
        return [
            BookingRead.model_validate(booking)
            for booking in list_user_bookings(session, current_user.id)
        ]

    @app.get(
        "/api/bookings/{booking_id}",
        response_model=BookingRead,
        tags=["Бронирования"],
        summary="Получить бронирование гостя",
    )
    def get_booking(
        booking_id: str,
        session: DbSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> BookingRead:
        try:
            booking = BookingService(session).get_user_booking(booking_id, current_user.id)
        except BookingNotFound as exc:
            raise HTTPException(status_code=404, detail="Booking not found.") from exc
        except BookingNotOwned as exc:
            raise HTTPException(
                status_code=403,
                detail="This booking belongs to another guest.",
            ) from exc
        return BookingRead.model_validate(booking)

    @app.delete(
        "/api/bookings/{booking_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["Бронирования"],
        summary="Отменить бронирование гостя",
    )
    def cancel_booking(
        booking_id: str,
        session: DbSession,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> Response:
        try:
            BookingService(session).cancel_booking(booking_id, current_user.id)
        except BookingNotFound as exc:
            raise HTTPException(status_code=404, detail="Booking not found.") from exc
        except BookingNotOwned as exc:
            raise HTTPException(
                status_code=403,
                detail="This booking belongs to another guest.",
            ) from exc
        except BookingStateConflict as exc:
            raise HTTPException(
                status_code=409,
                detail="This booking cannot be cancelled in its current state.",
            ) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app
