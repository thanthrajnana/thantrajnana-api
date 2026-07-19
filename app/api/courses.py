from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models import Course, CourseModule
from app.schemas import CourseDetail, CourseSummary, ModuleResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseSummary])
def list_courses(db: Session = Depends(get_db)):
    return db.scalars(select(Course).where(Course.is_published.is_(True)).order_by(Course.title)).all()


@router.get("/{slug}", response_model=CourseDetail)
def get_course(slug: str, db: Session = Depends(get_db)):
    course = db.scalar(
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{slug}/modules", response_model=list[ModuleResponse])
def get_modules(slug: str, db: Session = Depends(get_db)):
    course = db.scalar(
        select(Course)
        .where(Course.slug == slug, Course.is_published.is_(True))
        .options(selectinload(Course.modules).selectinload(CourseModule.lessons))
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course.modules
