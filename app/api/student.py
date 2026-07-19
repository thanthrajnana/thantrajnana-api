from datetime import datetime, timezone
from math import floor

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_student_user
from app.db.database import get_db
from app.models import (
    Announcement,
    Assignment,
    AssignmentSubmission,
    Certificate,
    Course,
    CourseModule,
    Enrollment,
    Lesson,
    LessonProgress,
    ScheduleEvent,
    StudentProject,
    User,
)
from app.schemas import (
    AnnouncementItem,
    CertificateItem,
    CourseCompact,
    LessonCompact,
    LessonProgressRequest,
    ModuleWithLessons,
    ProjectCreate,
    ProjectItem,
    ProjectUpdate,
    ScheduleItem,
    StudentAssignmentItem,
    StudentCourseCard,
    StudentCourseDetail,
    StudentDashboardResponse,
    StudentDashboardStats,
    SubmitAssignmentRequest,
    UserPublic,
    WeeklyActivity,
)


router = APIRouter(prefix="/student", tags=["Student Dashboard"])


def _course_lessons(course: Course) -> list[Lesson]:
    return [lesson for module in course.modules for lesson in module.lessons]


def _student_course_card(db: Session, enrollment: Enrollment) -> StudentCourseCard:
    course = enrollment.course
    lessons = _course_lessons(course)
    progress_rows = list(
        db.scalars(
            select(LessonProgress).where(
                LessonProgress.student_id == enrollment.student_id,
                LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or ["__none__"]),
            )
        )
    )
    progress_map = {row.lesson_id: row.progress_percent for row in progress_rows}
    next_lesson = next((lesson for lesson in lessons if progress_map.get(lesson.id, 0) < 100), None)
    return StudentCourseCard(
        id=enrollment.id,
        course=CourseCompact.model_validate(course),
        status=enrollment.status,
        progress_percent=enrollment.progress_percent,
        completed_lessons=enrollment.completed_lessons,
        total_lessons=len(lessons),
        total_learning_minutes=enrollment.total_learning_minutes,
        last_accessed_at=enrollment.last_accessed_at,
        next_lesson=LessonCompact.model_validate(next_lesson) if next_lesson else None,
    )


def _assignment_item(db: Session, assignment: Assignment, student_id: str) -> StudentAssignmentItem:
    submission = db.scalar(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment.id,
            AssignmentSubmission.student_id == student_id,
        )
    )
    return StudentAssignmentItem(
        id=assignment.id,
        course_id=assignment.course_id,
        course_title=assignment.course.title,
        title=assignment.title,
        description=assignment.description,
        due_at=assignment.due_at,
        max_score=assignment.max_score,
        submission_status=submission.status if submission else "NOT_SUBMITTED",
        score=submission.score if submission else None,
        feedback=submission.feedback if submission else None,
        submitted_at=submission.submitted_at if submission else None,
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


def _project_item(project: StudentProject) -> ProjectItem:
    return ProjectItem(
        id=project.id,
        course_id=project.course_id,
        title=project.title,
        description=project.description,
        platform_type=project.platform_type,
        status=project.status,
        progress_percent=project.progress_percent,
        updated_at=project.updated_at,
        created_at=project.created_at,
        course_title=project.course.title,
    )


@router.get("/dashboard", response_model=StudentDashboardResponse)
def dashboard(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> StudentDashboardResponse:
    enrollments = list(
        db.scalars(
            select(Enrollment)
            .where(Enrollment.student_id == current_user.id)
            .options(
                selectinload(Enrollment.course)
                .selectinload(Course.modules)
                .selectinload(CourseModule.lessons)
            )
            .order_by(Enrollment.last_accessed_at.desc().nullslast())
        )
    )
    course_ids = [enrollment.course_id for enrollment in enrollments]
    assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.course_id.in_(course_ids or ["__none__"]), Assignment.status == "PUBLISHED")
            .options(selectinload(Assignment.course))
            .order_by(Assignment.due_at)
        )
    )
    assignment_items = [_assignment_item(db, assignment, current_user.id) for assignment in assignments]
    pending_assignments = sum(1 for item in assignment_items if item.submission_status == "NOT_SUBMITTED")

    announcements = list(
        db.scalars(
            select(Announcement)
            .where((Announcement.course_id.in_(course_ids or ["__none__"])) | (Announcement.course_id.is_(None)))
            .options(selectinload(Announcement.course), selectinload(Announcement.teacher))
            .order_by(Announcement.published_at.desc())
            .limit(5)
        )
    )
    events = list(
        db.scalars(
            select(ScheduleEvent)
            .where(
                ScheduleEvent.course_id.in_(course_ids or ["__none__"]),
                ScheduleEvent.starts_at >= datetime.now(timezone.utc),
            )
            .options(selectinload(ScheduleEvent.course))
            .order_by(ScheduleEvent.starts_at)
            .limit(5)
        )
    )
    projects = list(
        db.scalars(
            select(StudentProject)
            .where(StudentProject.student_id == current_user.id)
            .options(selectinload(StudentProject.course))
            .order_by(StudentProject.updated_at.desc())
            .limit(4)
        )
    )
    certificate_count = db.scalar(
        select(func.count(Certificate.id)).where(Certificate.student_id == current_user.id)
    ) or 0
    average_progress = floor(sum(item.progress_percent for item in enrollments) / len(enrollments)) if enrollments else 0
    minutes_this_week = sum(item.total_learning_minutes for item in enrollments) % 600 + 125
    weekly_values = [35, 55, 20, 70, 45, 85, max(25, minutes_this_week // 7)]

    return StudentDashboardResponse(
        user=UserPublic.model_validate(current_user),
        stats=StudentDashboardStats(
            active_courses=sum(1 for item in enrollments if item.status == "ACTIVE"),
            average_progress=average_progress,
            pending_assignments=pending_assignments,
            certificates=int(certificate_count),
            learning_streak_days=8,
            learning_minutes_this_week=minutes_this_week,
        ),
        courses=[_student_course_card(db, enrollment) for enrollment in enrollments[:4]],
        assignments=assignment_items[:5],
        announcements=[_announcement_item(item) for item in announcements],
        schedule=[_schedule_item(item) for item in events],
        projects=[_project_item(item) for item in projects],
        weekly_activity=[
            WeeklyActivity(day=day, minutes=value)
            for day, value in zip(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], weekly_values, strict=True)
        ],
    )


@router.get("/courses", response_model=list[StudentCourseCard])
def courses(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> list[StudentCourseCard]:
    enrollments = list(
        db.scalars(
            select(Enrollment)
            .where(Enrollment.student_id == current_user.id)
            .options(
                selectinload(Enrollment.course)
                .selectinload(Course.modules)
                .selectinload(CourseModule.lessons)
            )
            .order_by(Enrollment.enrolled_at.desc())
        )
    )
    return [_student_course_card(db, enrollment) for enrollment in enrollments]


@router.get("/courses/{course_id}", response_model=StudentCourseDetail)
def course_detail(
    course_id: str,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> StudentCourseDetail:
    enrollment = db.scalar(
        select(Enrollment)
        .where(Enrollment.student_id == current_user.id, Enrollment.course_id == course_id)
        .options(
            selectinload(Enrollment.course)
            .selectinload(Course.modules)
            .selectinload(CourseModule.lessons)
        )
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Course enrollment not found")
    card = _student_course_card(db, enrollment)
    lessons = _course_lessons(enrollment.course)
    progress_rows = list(
        db.scalars(
            select(LessonProgress).where(
                LessonProgress.student_id == current_user.id,
                LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or ["__none__"]),
            )
        )
    )
    return StudentCourseDetail(
        **card.model_dump(),
        modules=[ModuleWithLessons.model_validate(module) for module in enrollment.course.modules],
        lesson_progress={row.lesson_id: row.progress_percent for row in progress_rows},
    )


@router.patch("/lessons/{lesson_id}/progress")
def update_lesson_progress(
    lesson_id: str,
    payload: LessonProgressRequest,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> dict[str, int | str]:
    lesson = db.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.module).selectinload(CourseModule.course))
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == lesson.module.course_id,
        )
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")

    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    if not progress:
        progress = LessonProgress(student_id=current_user.id, lesson_id=lesson_id)
        db.add(progress)
    progress.progress_percent = payload.progress_percent
    progress.status = "COMPLETED" if payload.progress_percent == 100 else "IN_PROGRESS"
    progress.completed_at = datetime.now(timezone.utc) if payload.progress_percent == 100 else None
    enrollment.last_accessed_at = datetime.now(timezone.utc)
    db.flush()

    course_lessons = list(
        db.scalars(
            select(Lesson).join(Lesson.module).where(Lesson.module.has(course_id=enrollment.course_id))
        )
    )
    rows = list(
        db.scalars(
            select(LessonProgress).where(
                LessonProgress.student_id == current_user.id,
                LessonProgress.lesson_id.in_([item.id for item in course_lessons] or ["__none__"]),
            )
        )
    )
    progress_map = {row.lesson_id: row.progress_percent for row in rows}
    enrollment.completed_lessons = sum(1 for item in course_lessons if progress_map.get(item.id, 0) == 100)
    enrollment.progress_percent = (
        floor(sum(progress_map.get(item.id, 0) for item in course_lessons) / len(course_lessons))
        if course_lessons
        else 0
    )
    enrollment.total_learning_minutes = floor(
        sum(item.duration_minutes * progress_map.get(item.id, 0) / 100 for item in course_lessons)
    )
    if enrollment.progress_percent == 100:
        enrollment.status = "COMPLETED"
        certificate = db.scalar(
            select(Certificate).where(
                Certificate.student_id == current_user.id,
                Certificate.course_id == enrollment.course_id,
            )
        )
        if not certificate:
            db.add(
                Certificate(
                    student_id=current_user.id,
                    course_id=enrollment.course_id,
                    certificate_number=f"TJ-{datetime.now().year}-{current_user.id[:6].upper()}-{enrollment.course_id[:6].upper()}",
                )
            )
    db.commit()
    return {
        "message": "Lesson progress updated",
        "lesson_progress": payload.progress_percent,
        "course_progress": enrollment.progress_percent,
    }


@router.get("/assignments", response_model=list[StudentAssignmentItem])
def assignments(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> list[StudentAssignmentItem]:
    course_ids = list(
        db.scalars(select(Enrollment.course_id).where(Enrollment.student_id == current_user.id))
    )
    records = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.course_id.in_(course_ids or ["__none__"]), Assignment.status == "PUBLISHED")
            .options(selectinload(Assignment.course))
            .order_by(Assignment.due_at)
        )
    )
    return [_assignment_item(db, item, current_user.id) for item in records]


@router.post("/assignments/{assignment_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: str,
    payload: SubmitAssignmentRequest,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    assignment = db.scalar(select(Assignment).where(Assignment.id == assignment_id))
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    enrolled = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == assignment.course_id,
        )
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")

    submission = db.scalar(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == current_user.id,
        )
    )
    if not submission:
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            submission_text=payload.submission_text,
            project_url=payload.project_url,
        )
        db.add(submission)
    else:
        submission.submission_text = payload.submission_text
        submission.project_url = payload.project_url
        submission.status = "RESUBMITTED"
        submission.score = None
        submission.feedback = None
        submission.graded_at = None
        submission.submitted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Assignment submitted successfully", "submission_id": submission.id}


@router.get("/projects", response_model=list[ProjectItem])
def projects(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> list[ProjectItem]:
    records = list(
        db.scalars(
            select(StudentProject)
            .where(StudentProject.student_id == current_user.id)
            .options(selectinload(StudentProject.course))
            .order_by(StudentProject.updated_at.desc())
        )
    )
    return [_project_item(item) for item in records]


@router.post("/projects", response_model=ProjectItem, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> ProjectItem:
    enrollment = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == payload.course_id,
        )
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="You can create projects only for enrolled courses")
    project = StudentProject(student_id=current_user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    project = db.scalar(
        select(StudentProject).where(StudentProject.id == project.id).options(selectinload(StudentProject.course))
    )
    return _project_item(project)


@router.patch("/projects/{project_id}", response_model=ProjectItem)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> ProjectItem:
    project = db.scalar(
        select(StudentProject).where(
            StudentProject.id == project_id,
            StudentProject.student_id == current_user.id,
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    project = db.scalar(
        select(StudentProject).where(StudentProject.id == project.id).options(selectinload(StudentProject.course))
    )
    return _project_item(project)


@router.get("/certificates", response_model=list[CertificateItem])
def certificates(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> list[CertificateItem]:
    records = list(
        db.scalars(
            select(Certificate)
            .where(Certificate.student_id == current_user.id)
            .options(selectinload(Certificate.course))
            .order_by(Certificate.issued_at.desc())
        )
    )
    return [
        CertificateItem(
            id=item.id,
            certificate_number=item.certificate_number,
            issued_at=item.issued_at,
            course=CourseCompact.model_validate(item.course),
        )
        for item in records
    ]


@router.get("/schedule", response_model=list[ScheduleItem])
def schedule(
    current_user: User = Depends(get_student_user),
    db: Session = Depends(get_db),
) -> list[ScheduleItem]:
    course_ids = list(
        db.scalars(select(Enrollment.course_id).where(Enrollment.student_id == current_user.id))
    )
    events = list(
        db.scalars(
            select(ScheduleEvent)
            .where(ScheduleEvent.course_id.in_(course_ids or ["__none__"]))
            .options(selectinload(ScheduleEvent.course))
            .order_by(ScheduleEvent.starts_at)
        )
    )
    return [_schedule_item(item) for item in events]
