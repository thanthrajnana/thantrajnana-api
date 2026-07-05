import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)

    category = Column(String(100), nullable=False)
    price = Column(Float, nullable=False, default=0)

    duration = Column(String(100), nullable=True)
    level = Column(String(50), nullable=True)

    has_kit = Column(Boolean, default=False)
    platform_type = Column(String(100), nullable=False)

    is_published = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    