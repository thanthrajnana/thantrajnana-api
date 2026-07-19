from datetime import datetime, timedelta, timezone
from math import floor

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_teacher_user
from app.db.database import get_db
from app.models import (
    Announcement,
    Assignment,
    AssignmentSubmission,
    Course,
    Enrollment,
    Lesson,
    ScheduleEvent,
    TeacherCourse,
    User,
)
from app.schemas import (
    AnnouncementCreate,
    AnnouncementItem,
    AssignmentCreate,
    GradeSubmissionRequest,
    ScheduleCreate,
    ScheduleItem,
    SubmissionItem,
    TeacherAssignmentItem,
    TeacherCourseCard,
    TeacherDashboardResponse,
    TeacherDashboardStats,
    TeacherStudentItem,
    TrendPoint,
    UserPublic,
)


router = APIRouter(prefix="/teacher", tags=["Teacher Dashboard"])


def _teacher_course_ids(db: Session, teacher_id: str) -> list[str]:
    return list(db.scalars(select(TeacherCourse.course_id).where(TeacherCourse.teacher_id == teacher_id)))


def _assert_teacher_course(db: Session, teacher_id: str, course_id: str) -> None:
    link = db.scalar(
        select(TeacherCourse.id).where(
            TeacherCourse.teacher_id == teacher_id,
            TeacherCourse.course_id == course_id,
        )
    )
    if not link:
        raise HTTPException(status_code=403, detail="You are not assigned to this course")


def _course_total_lessons(db: Session, course_id: str) -> int:
    return int(
        db.scalar(
            select(func.count(Lesson.id))
            .join(Lesson.module)
            .where(Lesson.module.has(course_id=course_id))
        )
        or 0
    )


def _teacher_student_item(db: Session, enrollment: Enrollment) -> TeacherStudentItem:
    total_lessons = _course_total_lessons(db, enrollment.course_id)
    return TeacherStudentItem(
        id=enrollment.student.id,
        first_name=enrollment.student.first_name,
        last_name=enrollment.student.last_name,
        email=enrollment.student.email,
        course_id=enrollment.course_id,
        course_title=enrollment.course.title,
        progress_percent=enrollment.progress_percent,
        completed_lessons=enrollment.completed_lessons,
        total_lessons=total_lessons,
        last_accessed_at=enrollment.last_accessed_at,
        status=enrollment.status,
    )


def _assignment_item(db: Session, assignment: Assignment) -> TeacherAssignmentItem:
    submission_count = int(
        db.scalar(
            select(func.count(AssignmentSubmission.id)).where(
                AssignmentSubmission.assignment_id == assignment.id
            )
        )
        or 0
    )
    graded_count = int(
        db.scalar(
            select(func.count(AssignmentSubmission.id)).where(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.status == "GRADED",
            )
        )
        or 0
    )
    return TeacherAssignmentItem(
        id=assignment.id,
        course_id=assignment.course_id,
        course_title=assignment.course.title,
        title=assignment.title,
        description=assignment.description,
        due_at=assignment.due_at,
        max_score=assignment.max_score,
        status=assignment.status,
        submission_count=submission_count,
        graded_count=graded_count,
        pending_count=max(0, submission_count - graded_count),
    )


def _submission_item(submission: AssignmentSubmission) -> SubmissionItem:
    return SubmissionItem(
        id=submission.id,
        assignment_id=submission.assignment_id,
        assignment_title=submission.assignment.title,
        course_title=submission.assignment.course.title,
        student_id=submission.student_id,
        student_name=f"{submission.student.first_name} {submission.student.last_name}",
        submission_text=submission.submission_text,
        project_url=submission.project_url,
        status=submission.status,
        score=submission.score,
        feedback=submission.feedback,
        submitted_at=submission.submitted_at,
        graded_at=submission.graded_at,
        max_score=submission.assignment.max_score,
    )


def _announcement_item(announcement: Announcement) -> AnnouncementItem:
    return AnnouncementItem(
        id=announcement.id,
        title=announcement.title,
        body=announcement.body,
        priority=announcement.priority,
        published_at=announcement.published_at,
        course_title=announcement.course.title if announcement.course else None,
        teacher_name=f"{announcement.teacher.first_name} {announcement.teacher.last_name}",
    )


def _schedule_item(event: ScheduleEvent) -> ScheduleItem:
    return ScheduleItem(
        id=event.id,
        title=event.title,
        event_type=event.event_type,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        meeting_url=event.meeting_url,
        course_title=event.course.title if event.course else None,
    )


def _teacher_course_card(db: Session, course: Course) -> TeacherCourseCard:
    enrollments = list(
        db.scalars(select(Enrollment).where(Enrollment.course_id == course.id))
    )
    average_progress = floor(sum(item.progress_percent for item in enrollments) / len(enrollments)) if enrollments else 0
    assignment_ids = list(db.scalars(select(Assignment.id).where(Assignment.course_id == course.id)))
    pending_reviews = int(
        db.scalar(
            select(func.count(AssignmentSubmission.id)).where(
                AssignmentSubmission.assignment_id.in_(assignment_ids or ["__none__"]),
                AssignmentSubmission.status.in_(["SUBMITTED", "RESUBMITTED"]),
            )
        )
        or 0
    )
    assignment_count = int(
        db.scalar(select(func.count(Assignment.id)).where(Assignment.course_id == course.id)) or 0
    )
    at_risk_count = sum(1 for enrollment in enrollments if enrollment.progress_percent < 35)
    from app.schemas import CourseCompact

    return TeacherCourseCard(
        id=course.id,
        course=CourseCompact.model_validate(course),
        student_count=len(enrollments),
        average_progress=average_progress,
        pending_reviews=pending_reviews,
        assignment_count=assignment_count,
        at_risk_count=at_risk_count,
    )


@router.get("/dashboard", response_model=TeacherDashboardResponse)
def dashboard(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> TeacherDashboardResponse:
    course_ids = _teacher_course_ids(db, current_user.id)
    courses = list(
        db.scalars(select(Course).where(Course.id.in_(course_ids or ["__none__"])).order_by(Course.title))
    )
    enrollments = list(
        db.scalars(
            select(Enrollment)
            .where(Enrollment.course_id.in_(course_ids or ["__none__"]))
            .options(selectinload(Enrollment.student), selectinload(Enrollment.course))
            .order_by(Enrollment.progress_percent)
        )
    )
    assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.teacher_id == current_user.id)
            .options(selectinload(Assignment.course))
        )
    )
    assignment_ids = [item.id for item in assignments]
    submissions = list(
        db.scalars(
            select(AssignmentSubmission)
            .where(AssignmentSubmission.assignment_id.in_(assignment_ids or ["__none__"]))
            .options(
                selectinload(AssignmentSubmission.student),
                selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course),
            )
            .order_by(AssignmentSubmission.submitted_at.desc())
            .limit(8)
        )
    )
    pending_reviews = sum(1 for item in submissions if item.status in {"SUBMITTED", "RESUBMITTED"})
    avg_completion = floor(sum(item.progress_percent for item in enrollments) / len(enrollments)) if enrollments else 0
    now = datetime.now(timezone.utc)
    next_week = now + timedelta(days=7)
    assignments_due = int(
        db.scalar(
            select(func.count(Assignment.id)).where(
                Assignment.teacher_id == current_user.id,
                Assignment.due_at >= now,
                Assignment.due_at <= next_week,
            )
        )
        or 0
    )
    announcements = list(
        db.scalars(
            select(Announcement)
            .where(Announcement.teacher_id == current_user.id)
            .options(selectinload(Announcement.course), selectinload(Announcement.teacher))
            .order_by(Announcement.published_at.desc())
            .limit(5)
        )
    )
    events = list(
        db.scalars(
            select(ScheduleEvent)
            .where(ScheduleEvent.owner_id == current_user.id, ScheduleEvent.starts_at >= now)
            .options(selectinload(ScheduleEvent.course))
            .order_by(ScheduleEvent.starts_at)
            .limit(5)
        )
    )
    at_risk = [item for item in enrollments if item.progress_percent < 40][:6]
    trend_base = max(4, len(enrollments) - 5)

    return TeacherDashboardResponse(
        user=UserPublic.model_validate(current_user),
        stats=TeacherDashboardStats(
            active_courses=len(courses),
            total_students=len({item.student_id for item in enrollments}),
            pending_reviews=pending_reviews,
            average_completion=avg_completion,
            assignments_due_this_week=assignments_due,
        ),
        courses=[_teacher_course_card(db, item) for item in courses],
        recent_submissions=[_submission_item(item) for item in submissions[:5]],
        at_risk_students=[_teacher_student_item(db, item) for item in at_risk],
        announcements=[_announcement_item(item) for item in announcements],
        schedule=[_schedule_item(item) for item in events],
        enrollment_trend=[
            TrendPoint(label=label, value=value)
            for label, value in zip(
                ["Feb", "Mar", "Apr", "May", "Jun", "Jul"],
                [trend_base, trend_base + 2, trend_base + 3, trend_base + 6, trend_base + 8, len(enrollments)],
                strict=True,
            )
        ],
    )


@router.get("/courses", response_model=list[TeacherCourseCard])
def courses(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[TeacherCourseCard]:
    course_ids = _teacher_course_ids(db, current_user.id)
    records = list(
        db.scalars(select(Course).where(Course.id.in_(course_ids or ["__none__"])).order_by(Course.title))
    )
    return [_teacher_course_card(db, item) for item in records]


@router.get("/students", response_model=list[TeacherStudentItem])
def students(
    course_id: str | None = None,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[TeacherStudentItem]:
    course_ids = _teacher_course_ids(db, current_user.id)
    if course_id:
        _assert_teacher_course(db, current_user.id, course_id)
        course_ids = [course_id]
    records = list(
        db.scalars(
            select(Enrollment)
            .where(Enrollment.course_id.in_(course_ids or ["__none__"]))
            .options(selectinload(Enrollment.student), selectinload(Enrollment.course))
            .order_by(User.first_name if False else Enrollment.progress_percent.desc())
        )
    )
    return [_teacher_student_item(db, item) for item in records]


@router.get("/assignments", response_model=list[TeacherAssignmentItem])
def assignments(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[TeacherAssignmentItem]:
    records = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.teacher_id == current_user.id)
            .options(selectinload(Assignment.course))
            .order_by(Assignment.due_at.desc())
        )
    )
    return [_assignment_item(db, item) for item in records]


@router.post("/assignments", response_model=TeacherAssignmentItem, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> TeacherAssignmentItem:
    _assert_teacher_course(db, current_user.id, payload.course_id)
    assignment = Assignment(teacher_id=current_user.id, status="PUBLISHED", **payload.model_dump())
    db.add(assignment)
    db.commit()
    assignment = db.scalar(
        select(Assignment).where(Assignment.id == assignment.id).options(selectinload(Assignment.course))
    )
    return _assignment_item(db, assignment)


@router.get("/submissions", response_model=list[SubmissionItem])
def submissions(
    status_filter: str | None = None,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[SubmissionItem]:
    assignment_ids = list(
        db.scalars(select(Assignment.id).where(Assignment.teacher_id == current_user.id))
    )
    query = (
        select(AssignmentSubmission)
        .where(AssignmentSubmission.assignment_id.in_(assignment_ids or ["__none__"]))
        .options(
            selectinload(AssignmentSubmission.student),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course),
        )
        .order_by(AssignmentSubmission.submitted_at.desc())
    )
    if status_filter:
        query = query.where(AssignmentSubmission.status == status_filter)
    return [_submission_item(item) for item in db.scalars(query)]


@router.patch("/submissions/{submission_id}/grade", response_model=SubmissionItem)
def grade_submission(
    submission_id: str,
    payload: GradeSubmissionRequest,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> SubmissionItem:
    submission = db.scalar(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(
            selectinload(AssignmentSubmission.student),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course),
        )
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot grade this submission")
    if payload.score > submission.assignment.max_score:
        raise HTTPException(
            status_code=422,
            detail=f"Score cannot be greater than {submission.assignment.max_score}",
        )
    submission.score = payload.score
    submission.feedback = payload.feedback
    submission.status = "GRADED"
    submission.graded_at = datetime.now(timezone.utc)
    db.commit()
    return _submission_item(submission)


@router.get("/announcements", response_model=list[AnnouncementItem])
def announcements(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[AnnouncementItem]:
    records = list(
        db.scalars(
            select(Announcement)
            .where(Announcement.teacher_id == current_user.id)
            .options(selectinload(Announcement.course), selectinload(Announcement.teacher))
            .order_by(Announcement.published_at.desc())
        )
    )
    return [_announcement_item(item) for item in records]


@router.post("/announcements", response_model=AnnouncementItem, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> AnnouncementItem:
    if payload.course_id:
        _assert_teacher_course(db, current_user.id, payload.course_id)
    announcement = Announcement(teacher_id=current_user.id, **payload.model_dump())
    db.add(announcement)
    db.commit()
    announcement = db.scalar(
        select(Announcement)
        .where(Announcement.id == announcement.id)
        .options(selectinload(Announcement.course), selectinload(Announcement.teacher))
    )
    return _announcement_item(announcement)


@router.get("/schedule", response_model=list[ScheduleItem])
def schedule(
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> list[ScheduleItem]:
    records = list(
        db.scalars(
            select(ScheduleEvent)
            .where(ScheduleEvent.owner_id == current_user.id)
            .options(selectinload(ScheduleEvent.course))
            .order_by(ScheduleEvent.starts_at)
        )
    )
    return [_schedule_item(item) for item in records]


@router.post("/schedule", response_model=ScheduleItem, status_code=status.HTTP_201_CREATED)
def create_schedule_event(
    payload: ScheduleCreate,
    current_user: User = Depends(get_teacher_user),
    db: Session = Depends(get_db),
) -> ScheduleItem:
    if payload.course_id:
        _assert_teacher_course(db, current_user.id, payload.course_id)
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="End time must be after start time")
    event = ScheduleEvent(owner_id=current_user.id, **payload.model_dump())
    db.add(event)
    db.commit()
    event = db.scalar(
        select(ScheduleEvent).where(ScheduleEvent.id == event.id).options(selectinload(ScheduleEvent.course))
    )
    return _schedule_item(event)
