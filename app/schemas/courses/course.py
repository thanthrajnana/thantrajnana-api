from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    title: str
    slug: str
    description: str

    category: str

    price: float

    duration: str | None = None

    level: str | None = None

    has_kit: bool = False

    platform_type: str

    is_published: bool = True


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    duration: str | None = None
    level: str | None = None
    has_kit: bool | None = None
    platform_type: str | None = None
    is_published: bool | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    title: str
    slug: str
    description: str

    category: str

    price: float

    duration: str | None

    level: str | None

    has_kit: bool

    platform_type: str

    is_published: bool
    