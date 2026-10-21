"""Database engine and session setup."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from yaotel.models import Base, Room


def create_database(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """Create an engine, schema, and session factory for a database URL."""
    if database_url.startswith("sqlite:///./"):
        Path(database_url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)

    engine_options: dict[str, object] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            engine_options["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_options)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    seed_rooms(factory)
    return engine, factory


def seed_rooms(factory: sessionmaker[Session]) -> None:
    """Insert deterministic demo rooms only when the catalog is empty."""
    with factory() as session:
        if session.query(Room.id).first() is not None:
            return
        session.add_all(
            [
                Room(number="101", category="Standard", capacity=2, base_price_kopecks=850_000),
                Room(number="102", category="Deluxe", capacity=2, base_price_kopecks=1_250_000),
                Room(number="201", category="Family", capacity=4, base_price_kopecks=1_750_000),
                Room(number="202", category="Suite", capacity=3, base_price_kopecks=2_500_000),
            ]
        )
        session.commit()
