from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    avatar_initials: str
    headline: str | None
    bio: str | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class CourseCompact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    category: str
    description: str
    platform_type: str
    accent: str
    level: str
    duration_weeks: int


class LessonCompact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    lesson_type: str
    duration_minutes: int
    order_no: int


class ModuleWithLessons(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    order_no: int
    lessons: list[LessonCompact]


class StudentCourseCard(BaseModel):
    id: str
    course: CourseCompact
    status: str
    progress_percent: int
    completed_lessons: int
    total_lessons: int
    total_learning_minutes: int
    last_accessed_at: datetime | None
    next_lesson: LessonCompact | None


class StudentCourseDetail(StudentCourseCard):
    modules: list[ModuleWithLessons]
    lesson_progress: dict[str, int]


class StudentAssignmentItem(BaseModel):
    id: str
    course_id: str
    course_title: str
    title: str
    description: str
    due_at: datetime
    max_score: int
    submission_status: str
    score: int | None
    feedback: str | None
    submitted_at: datetime | None


class SubmitAssignmentRequest(BaseModel):
    submission_text: str = Field(min_length=10, max_length=8000)
    project_url: str | None = Field(default=None, max_length=500)


class LessonProgressRequest(BaseModel):
    progress_percent: int = Field(ge=0, le=100)


class ProjectCreate(BaseModel):
    course_id: str
    title: str = Field(min_length=3, max_length=220)
    description: str = Field(default="", max_length=2000)
    platform_type: str = Field(min_length=2, max_length=60)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=220)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)


class ProjectItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    title: str
    description: str
    platform_type: str
    status: str
    progress_percent: int
    updated_at: datetime
    created_at: datetime
    course_title: str | None = None


class CertificateItem(BaseModel):
    id: str
    certificate_number: str
    issued_at: datetime
    course: CourseCompact


class AnnouncementItem(BaseModel):
    id: str
    title: str
    body: str
    priority: str
    published_at: datetime
    course_title: str | None
    teacher_name: str


class ScheduleItem(BaseModel):
    id: str
    title: str
    event_type: str
    starts_at: datetime
    ends_at: datetime
    meeting_url: str | None
    course_title: str | None


class WeeklyActivity(BaseModel):
    day: str
    minutes: int


class StudentDashboardStats(BaseModel):
    active_courses: int
    average_progress: int
    pending_assignments: int
    certificates: int
    learning_streak_days: int
    learning_minutes_this_week: int


class StudentDashboardResponse(BaseModel):
    user: UserPublic
    stats: StudentDashboardStats
    courses: list[StudentCourseCard]
    assignments: list[StudentAssignmentItem]
    announcements: list[AnnouncementItem]
    schedule: list[ScheduleItem]
    projects: list[ProjectItem]
    weekly_activity: list[WeeklyActivity]


class TeacherCourseCard(BaseModel):
    id: str
    course: CourseCompact
    student_count: int
    average_progress: int
    pending_reviews: int
    assignment_count: int
    at_risk_count: int


class TeacherStudentItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    course_id: str
    course_title: str
    progress_percent: int
    completed_lessons: int
    total_lessons: int
    last_accessed_at: datetime | None
    status: str


class TeacherAssignmentItem(BaseModel):
    id: str
    course_id: str
    course_title: str
    title: str
    description: str
    due_at: datetime
    max_score: int
    status: str
    submission_count: int
    graded_count: int
    pending_count: int


class AssignmentCreate(BaseModel):
    course_id: str
    title: str = Field(min_length=3, max_length=220)
    description: str = Field(min_length=10, max_length=8000)
    due_at: datetime
    max_score: int = Field(default=100, ge=1, le=1000)


class SubmissionItem(BaseModel):
    id: str
    assignment_id: str
    assignment_title: str
    course_title: str
    student_id: str
    student_name: str
    submission_text: str
    project_url: str | None
    status: str
    score: int | None
    feedback: str | None
    submitted_at: datetime
    graded_at: datetime | None
    max_score: int


class GradeSubmissionRequest(BaseModel):
    score: int = Field(ge=0)
    feedback: str = Field(min_length=3, max_length=4000)


class AnnouncementCreate(BaseModel):
    course_id: str | None = None
    title: str = Field(min_length=3, max_length=220)
    body: str = Field(min_length=10, max_length=8000)
    priority: str = "NORMAL"


class ScheduleCreate(BaseModel):
    course_id: str | None = None
    title: str = Field(min_length=3, max_length=220)
    event_type: str = "LIVE_CLASS"
    starts_at: datetime
    ends_at: datetime
    meeting_url: str | None = Field(default=None, max_length=500)


class TeacherDashboardStats(BaseModel):
    active_courses: int
    total_students: int
    pending_reviews: int
    average_completion: int
    assignments_due_this_week: int


class TrendPoint(BaseModel):
    label: str
    value: int


class TeacherDashboardResponse(BaseModel):
    user: UserPublic
    stats: TeacherDashboardStats
    courses: list[TeacherCourseCard]
    recent_submissions: list[SubmissionItem]
    at_risk_students: list[TeacherStudentItem]
    announcements: list[AnnouncementItem]
    schedule: list[ScheduleItem]
    enrollment_trend: list[TrendPoint]


# Public website / commerce schemas
from decimal import Decimal

class UserRegister(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    first_name: str
    last_name: str | None
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None
    lesson_type: str
    duration_minutes: int
    order_no: int
    is_free_preview: bool


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None
    order_no: int
    lessons: list[LessonResponse]


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    slug: str
    short_description: str
    category: str
    price: Decimal
    duration: str
    level: str
    has_kit: bool
    kit_name: str | None
    platform_type: str
    is_published: bool


class CourseDetail(CourseSummary):
    description: str
    modules: list[ModuleResponse]


class CheckoutRequest(BaseModel):
    course_id: str
    payment_method: str = "MOCK"


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_number: str
    status: str
    total_amount: Decimal
    course_id: str
    enrollment_id: str


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    progress_percent: int
    course: CourseSummary
