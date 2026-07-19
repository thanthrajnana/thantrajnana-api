from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _resolve_database_url(raw_url: str) -> str:
    # SQLAlchemy defaults postgresql:// to psycopg2. This project uses psycopg v3.
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


resolved_database_url = _resolve_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if resolved_database_url.startswith("sqlite") else {}

engine = create_engine(
    resolved_database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
