import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name = Column(
        String(100),
        nullable=False,
    )

    last_name = Column(
        String(100),
        nullable=True,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    phone = Column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    profile_image_url = Column(
        String(500),
        nullable=True,
    )

    email_verified = Column(
        Boolean,
        default=False,
    )

    phone_verified = Column(
        Boolean,
        default=False,
    )

    status = Column(
        String(30),
        default="ACTIVE",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    