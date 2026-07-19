from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Course
from app.schemas import CourseCompact


router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/courses", response_model=list[CourseCompact])
def list_courses(db: Session = Depends(get_db)) -> list[Course]:
    return list(db.scalars(select(Course).where(Course.is_published.is_(True)).order_by(Course.title)))
