import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    avatar_initials: Mapped[str] = mapped_column(String(4), default="TJ")
    headline: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", foreign_keys="Enrollment.student_id"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    teaching_courses: Mapped[list["TeacherCourse"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan", foreign_keys="TeacherCourse.teacher_id"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    short_description: Mapped[str] = mapped_column(String(400), default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    platform_type: Mapped[str] = mapped_column(String(60), nullable=False)
    accent: Mapped[str] = mapped_column(String(30), default="cyan")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), default="12 weeks")
    has_kit: Mapped[bool] = mapped_column(Boolean, default=False)
    kit_name: Mapped[str | None] = mapped_column(String(150))
    level: Mapped[str] = mapped_column(String(50), default="Beginner")
    duration_weeks: Mapped[int] = mapped_column(Integer, default=12)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    modules: Mapped[list["CourseModule"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.order_no"
    )
    teacher_links: Mapped[list["TeacherCourse"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class CourseModule(Base):
    __tablename__ = "course_modules"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_no: Mapped[int] = mapped_column(Integer, default=1)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order_no"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    module_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("course_modules.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lesson_type: Mapped[str] = mapped_column(String(30), default="VIDEO")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15)
    order_no: Mapped[int] = mapped_column(Integer, default=1)
    is_free_preview: Mapped[bool] = mapped_column(Boolean, default=False)

    module: Mapped[CourseModule] = relationship(back_populates="lessons")


class TeacherCourse(Base):
    __tablename__ = "teacher_courses"
    __table_args__ = (UniqueConstraint("teacher_id", "course_id", name="uq_teacher_course"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    teacher_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher: Mapped[User] = relationship(back_populates="teaching_courses", foreign_keys=[teacher_id])
    course: Mapped[Course] = relationship(back_populates="teacher_links")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    student_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_lessons: Mapped[int] = mapped_column(Integer, default=0)
    total_learning_minutes: Mapped[int] = mapped_column(Integer, default=0)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[User] = relationship(back_populates="enrollments", foreign_keys=[student_id])
    course: Mapped[Course] = relationship(back_populates="enrollments")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    student_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="NOT_STARTED")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lesson: Mapped[Lesson] = relationship()


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    teacher_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(30), default="PUBLISHED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship()
    teacher: Mapped[User] = relationship(foreign_keys=[teacher_id])
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    assignment_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    submission_text: Mapped[str] = mapped_column(Text, nullable=False)
    project_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", index=True)
    score: Mapped[int | None] = mapped_column(Integer)
    feedback: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship(foreign_keys=[student_id])


class StudentProject(Base):
    __tablename__ = "student_projects"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    student_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    platform_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="IN_PROGRESS", index=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship()


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_certificate_student_course"),)

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    student_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    certificate_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Course] = relationship()


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    teacher_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="NORMAL")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher: Mapped[User] = relationship(foreign_keys=[teacher_id])
    course: Mapped[Course | None] = relationship()


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    owner_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), default="LIVE_CLASS")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meeting_url: Mapped[str | None] = mapped_column(String(500))

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    course: Mapped[Course | None] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="PAID", index=True)
    payment_method: Mapped[str] = mapped_column(String(30), default="MOCK")
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=uuid_str)
    order_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    order: Mapped[Order] = relationship(back_populates="items")


class StudioProject(Base):
    __tablename__ = "scratch_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    board_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    workspace_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WebScratchProject(Base):
    __tablename__ = "web_scratch_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(80), nullable=False, default="blank", index=True)
    workspace_json: Mapped[str] = mapped_column(Text, nullable=False)
    html_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    css_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    javascript_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
