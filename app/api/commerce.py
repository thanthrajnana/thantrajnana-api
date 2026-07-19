from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models import Course, Enrollment, Order, OrderItem, User
from app.schemas import CheckoutRequest, EnrollmentResponse, OrderResponse

router = APIRouter(tags=["Commerce & Learning"])


@router.post("/orders/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.get(Course, payload.course_id)
    if not course or not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course.id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="You are already enrolled in this course")

    order = Order(
        order_number=f"THN-{datetime.utcnow():%Y%m%d%H%M%S%f}",
        user_id=current_user.id,
        status="PAID",
        payment_method=payload.payment_method.upper(),
        total_amount=course.price,
    )
    order.items.append(OrderItem(course_id=course.id, title=course.title, unit_price=course.price, quantity=1))
    enrollment = Enrollment(student_id=current_user.id, course_id=course.id)
    db.add_all([order, enrollment])
    db.commit()
    db.refresh(order)
    db.refresh(enrollment)
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        course_id=course.id,
        enrollment_id=enrollment.id,
    )


@router.get("/enrollments/me", response_model=list[EnrollmentResponse])
def my_enrollments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.scalars(
        select(Enrollment)
        .where(Enrollment.student_id == current_user.id)
        .options(selectinload(Enrollment.course))
        .order_by(Enrollment.enrolled_at.desc())
    ).all()
