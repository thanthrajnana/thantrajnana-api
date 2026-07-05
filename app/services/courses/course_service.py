from fastapi import HTTPException

from app.models.courses.course import Course
from app.repositories.courses.course_repository import CourseRepository
from app.schemas.courses.course import CourseCreate


class CourseService:

    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def get_courses(self):
        return self.repository.get_all()

    def get_course(self, slug: str):
        course = self.repository.get_by_slug(slug)

        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found",
            )

        return course

    def create_course(self, payload: CourseCreate):

        existing = self.repository.get_by_slug(payload.slug)

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Course already exists",
            )

        course = Course(**payload.model_dump())

        return self.repository.create(course)
    