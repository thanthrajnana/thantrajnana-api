from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.repositories.courses.course_repository import CourseRepository
from app.schemas.courses.course import (
    CourseCreate,
    CourseResponse,
)
from app.services.courses.course_service import CourseService

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.get(
    "/",
    response_model=list[CourseResponse],
)
def get_courses(
    db: Session = Depends(get_db),
):
    service = CourseService(
        CourseRepository(db),
    )

    return service.get_courses()


@router.get(
    "/{slug}",
    response_model=CourseResponse,
)
def get_course(
    slug: str,
    db: Session = Depends(get_db),
):
    service = CourseService(
        CourseRepository(db),
    )

    return service.get_course(slug)


@router.post(
    "/",
    response_model=CourseResponse,
)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
):
    service = CourseService(
        CourseRepository(db),
    )

    return service.create_course(payload)
