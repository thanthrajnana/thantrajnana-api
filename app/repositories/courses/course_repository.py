from sqlalchemy.orm import Session

from app.models.courses.course import Course


class CourseRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return (
            self.db.query(Course)
            .filter(Course.is_published == True)
            .all()
        )

    def get_by_slug(self, slug: str):
        return (
            self.db.query(Course)
            .filter(Course.slug == slug)
            .first()
        )

    def create(self, course: Course):
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course
    