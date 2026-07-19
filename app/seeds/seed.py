from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
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
    TeacherCourse,
    User,
)


COURSE_DATA = [
    {
        "title": "Web Development",
        "slug": "web-development",
        "category": "Software",
        "description": "Build responsive websites using visual blocks while learning HTML, CSS and JavaScript concepts.",
        "platform_type": "WEB_BUILDER",
        "accent": "violet",
        "level": "Beginner",
        "duration_weeks": 12,
    },
    {
        "title": "IoT with ESP32",
        "slug": "iot-with-esp32",
        "category": "IoT",
        "description": "Connect sensors, Wi-Fi and cloud services using ESP32 and the Thantrajnana IoT builder.",
        "platform_type": "ESP32_BUILDER",
        "accent": "cyan",
        "level": "Intermediate",
        "duration_weeks": 14,
    },
    {
        "title": "Arduino Embedded Systems",
        "slug": "arduino-embedded-systems",
        "category": "Embedded",
        "description": "Learn digital electronics, sensors and actuators through practical Arduino projects.",
        "platform_type": "ARDUINO_BUILDER",
        "accent": "amber",
        "level": "Beginner",
        "duration_weeks": 12,
    },
    {
        "title": "Robotics with Arduino",
        "slug": "robotics-with-arduino",
        "category": "Robotics",
        "description": "Create autonomous robots using motors, sensors and visual programming.",
        "platform_type": "ROBOTICS_BUILDER",
        "accent": "rose",
        "level": "Intermediate",
        "duration_weeks": 16,
    },
]

MODULE_TEMPLATES = [
    (
        "Foundations",
        [
            ("Course orientation", "VIDEO", 12),
            ("Visual coding essentials", "INTERACTIVE", 24),
        ],
    ),
    (
        "Build with confidence",
        [
            ("Components and data flow", "ARTICLE", 20),
            ("Guided practice lab", "LAB", 40),
        ],
    ),
    (
        "Capstone project",
        [
            ("Plan your solution", "PROJECT", 30),
            ("Build, test and present", "PROJECT", 75),
        ],
    ),
]


def seed_database(db: Session) -> None:
    if db.scalar(select(User).where(User.email == "teacher@thantrajnana.com")):
        return

    teacher = User(
        first_name="Ananya",
        last_name="Rao",
        email="teacher@thantrajnana.com",
        password_hash=hash_password("Teacher@123"),
        role="TEACHER",
        avatar_initials="AR",
        headline="STEM Educator and Robotics Mentor",
        bio="I help students turn ideas into working software, IoT systems and robots.",
    )
    students = [
        User(
            first_name="Demo",
            last_name="Student",
            email="student@thantrajnana.com",
            password_hash=hash_password("Student@123"),
            role="STUDENT",
            avatar_initials="DS",
            headline="Young Innovator",
            bio="Learning web development, IoT and robotics one project at a time.",
        ),
        User(first_name="Aarav", last_name="Kumar", email="aarav@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="AK", headline="Web Explorer"),
        User(first_name="Diya", last_name="Sharma", email="diya@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="DS", headline="IoT Creator"),
        User(first_name="Rohan", last_name="Nair", email="rohan@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="RN", headline="Arduino Maker"),
        User(first_name="Meera", last_name="Iyer", email="meera@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="MI", headline="Robotics Learner"),
        User(first_name="Kabir", last_name="Singh", email="kabir@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="KS", headline="Future Engineer"),
        User(first_name="Isha", last_name="Patel", email="isha@thantrajnana.com", password_hash=hash_password("Student@123"), role="STUDENT", avatar_initials="IP", headline="Creative Coder"),
    ]
    db.add(teacher)
    db.add_all(students)
    db.flush()

    courses: list[Course] = []
    lessons_by_course: dict[str, list[Lesson]] = {}
    for course_data in COURSE_DATA:
        course = Course(**course_data)
        db.add(course)
        db.flush()
        courses.append(course)
        lessons_by_course[course.id] = []
        for module_index, (module_title, lessons) in enumerate(MODULE_TEMPLATES, start=1):
            module = CourseModule(course_id=course.id, title=module_title, order_no=module_index)
            db.add(module)
            db.flush()
            for lesson_index, (lesson_title, lesson_type, minutes) in enumerate(lessons, start=1):
                lesson = Lesson(
                    module_id=module.id,
                    title=f"{lesson_title}: {course.title}",
                    lesson_type=lesson_type,
                    duration_minutes=minutes,
                    order_no=lesson_index,
                )
                db.add(lesson)
                db.flush()
                lessons_by_course[course.id].append(lesson)
        db.add(TeacherCourse(teacher_id=teacher.id, course_id=course.id))

    db.flush()
    now = datetime.now(timezone.utc)
    progress_matrix = {
        students[0].email: [82, 57, 34, 100],
        students[1].email: [68, 42, 0, 0],
        students[2].email: [91, 76, 44, 0],
        students[3].email: [39, 28, 73, 35],
        students[4].email: [84, 61, 55, 79],
        students[5].email: [24, 18, 31, 22],
        students[6].email: [96, 70, 62, 48],
    }

    enrollment_map: dict[tuple[str, str], Enrollment] = {}
    for student_index, student in enumerate(students):
        percentages = progress_matrix[student.email]
        for course_index, course in enumerate(courses):
            progress = percentages[course_index]
            if progress == 0 and student_index not in {0, 3, 4, 5, 6}:
                continue
            lessons = lessons_by_course[course.id]
            completed = min(len(lessons), int((progress / 100) * len(lessons)))
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id,
                status="COMPLETED" if progress == 100 else "ACTIVE",
                progress_percent=progress,
                completed_lessons=completed,
                total_learning_minutes=int(sum(item.duration_minutes for item in lessons) * progress / 100),
                last_accessed_at=now - timedelta(days=(student_index + course_index) % 9, hours=course_index * 2),
            )
            db.add(enrollment)
            db.flush()
            enrollment_map[(student.id, course.id)] = enrollment

            remaining = progress
            for lesson in lessons:
                lesson_progress = min(100, max(0, remaining))
                if lesson_progress > 0:
                    db.add(
                        LessonProgress(
                            student_id=student.id,
                            lesson_id=lesson.id,
                            status="COMPLETED" if lesson_progress == 100 else "IN_PROGRESS",
                            progress_percent=lesson_progress,
                            completed_at=(now - timedelta(days=course_index + 2)) if lesson_progress == 100 else None,
                        )
                    )
                remaining -= 100

    db.flush()

    assignments = [
        Assignment(
            course_id=courses[0].id,
            teacher_id=teacher.id,
            title="Responsive portfolio website",
            description="Create a personal portfolio with a hero section, project cards, responsive navigation and contact form.",
            due_at=now + timedelta(days=3),
            max_score=100,
        ),
        Assignment(
            course_id=courses[1].id,
            teacher_id=teacher.id,
            title="ESP32 climate dashboard",
            description="Read temperature and humidity values and display them on a browser dashboard over Wi-Fi.",
            due_at=now + timedelta(days=5),
            max_score=100,
        ),
        Assignment(
            course_id=courses[2].id,
            teacher_id=teacher.id,
            title="Arduino traffic light controller",
            description="Build and document a safe traffic-light state machine with pedestrian crossing support.",
            due_at=now - timedelta(days=2),
            max_score=100,
        ),
        Assignment(
            course_id=courses[3].id,
            teacher_id=teacher.id,
            title="Obstacle-avoiding rover",
            description="Create navigation logic using an ultrasonic sensor and dual motor driver.",
            due_at=now + timedelta(days=8),
            max_score=120,
        ),
    ]
    db.add_all(assignments)
    db.flush()

    submissions = [
        AssignmentSubmission(
            assignment_id=assignments[0].id,
            student_id=students[0].id,
            submission_text="I created the full portfolio with responsive navigation, project cards and accessible form labels.",
            project_url="https://example.com/demo-portfolio",
            status="SUBMITTED",
            submitted_at=now - timedelta(hours=4),
        ),
        AssignmentSubmission(
            assignment_id=assignments[2].id,
            student_id=students[0].id,
            submission_text="Traffic-light states are implemented with non-blocking millis timing and pedestrian input.",
            status="GRADED",
            score=88,
            feedback="Strong state-machine design. Add a short debounce explanation to the documentation.",
            submitted_at=now - timedelta(days=4),
            graded_at=now - timedelta(days=2),
        ),
        AssignmentSubmission(
            assignment_id=assignments[0].id,
            student_id=students[1].id,
            submission_text="Portfolio includes mobile navigation, skills section and three project case studies.",
            project_url="https://example.com/aarav-portfolio",
            status="SUBMITTED",
            submitted_at=now - timedelta(hours=7),
        ),
        AssignmentSubmission(
            assignment_id=assignments[1].id,
            student_id=students[2].id,
            submission_text="ESP32 publishes DHT22 readings every five seconds and the dashboard renders trend cards.",
            status="RESUBMITTED",
            submitted_at=now - timedelta(hours=12),
        ),
        AssignmentSubmission(
            assignment_id=assignments[2].id,
            student_id=students[3].id,
            submission_text="Completed the three-light sequence and added a push-button pedestrian mode.",
            status="SUBMITTED",
            submitted_at=now - timedelta(days=1),
        ),
        AssignmentSubmission(
            assignment_id=assignments[3].id,
            student_id=students[4].id,
            submission_text="Rover measures left and right distances before selecting the clearest turn direction.",
            project_url="https://example.com/meera-rover",
            status="GRADED",
            score=108,
            feedback="Excellent sensor scanning and clear explanation of motor control decisions.",
            submitted_at=now - timedelta(days=3),
            graded_at=now - timedelta(days=1),
        ),
    ]
    db.add_all(submissions)

    projects = [
        StudentProject(student_id=students[0].id, course_id=courses[0].id, title="My creative portfolio", description="Responsive portfolio generated with the web visual builder.", platform_type="WEB_BUILDER", status="IN_PROGRESS", progress_percent=78),
        StudentProject(student_id=students[0].id, course_id=courses[1].id, title="Smart climate monitor", description="ESP32 dashboard for temperature and humidity monitoring.", platform_type="ESP32_BUILDER", status="IN_PROGRESS", progress_percent=62),
        StudentProject(student_id=students[0].id, course_id=courses[2].id, title="Traffic light controller", description="Arduino state-machine project with pedestrian mode.", platform_type="ARDUINO_BUILDER", status="COMPLETED", progress_percent=100),
        StudentProject(student_id=students[0].id, course_id=courses[3].id, title="Obstacle avoiding rover", description="Two-wheel robot using ultrasonic navigation.", platform_type="ROBOTICS_BUILDER", status="IN_PROGRESS", progress_percent=35),
    ]
    db.add_all(projects)

    db.add(
        Certificate(
            student_id=students[0].id,
            course_id=courses[3].id,
            certificate_number=f"TJ-{now.year}-ROBO-{students[0].id[:6].upper()}",
            issued_at=now - timedelta(days=14),
        )
    )

    announcements = [
        Announcement(teacher_id=teacher.id, course_id=courses[0].id, title="Portfolio review clinic", body="Bring your current portfolio project to Thursday's live review. We will focus on mobile responsiveness and accessibility.", priority="HIGH", published_at=now - timedelta(hours=5)),
        Announcement(teacher_id=teacher.id, course_id=courses[1].id, title="ESP32 kit checklist", body="Please confirm that your DHT sensor, jumper wires and USB cable are ready before the next lab.", priority="NORMAL", published_at=now - timedelta(days=1)),
        Announcement(teacher_id=teacher.id, course_id=courses[3].id, title="Robotics challenge week", body="This week's optional challenge is to make your rover choose the direction with the greatest free distance.", priority="NORMAL", published_at=now - timedelta(days=2)),
        Announcement(teacher_id=teacher.id, course_id=None, title="Monthly showcase registrations open", body="Submit your best project for the Thantrajnana student showcase before the end of this month.", priority="HIGH", published_at=now - timedelta(days=3)),
    ]
    db.add_all(announcements)

    schedule = [
        ScheduleEvent(owner_id=teacher.id, course_id=courses[0].id, title="Live portfolio review", event_type="LIVE_CLASS", starts_at=now + timedelta(days=1, hours=3), ends_at=now + timedelta(days=1, hours=4), meeting_url="https://meet.example.com/portfolio-review"),
        ScheduleEvent(owner_id=teacher.id, course_id=courses[1].id, title="ESP32 sensor lab", event_type="LAB", starts_at=now + timedelta(days=2, hours=2), ends_at=now + timedelta(days=2, hours=3, minutes=30), meeting_url="https://meet.example.com/esp32-lab"),
        ScheduleEvent(owner_id=teacher.id, course_id=courses[2].id, title="Arduino doubt-clearing session", event_type="MENTORING", starts_at=now + timedelta(days=4, hours=1), ends_at=now + timedelta(days=4, hours=2), meeting_url="https://meet.example.com/arduino-mentor"),
        ScheduleEvent(owner_id=teacher.id, course_id=courses[3].id, title="Robotics project checkpoint", event_type="PROJECT_REVIEW", starts_at=now + timedelta(days=6, hours=3), ends_at=now + timedelta(days=6, hours=4), meeting_url="https://meet.example.com/robotics-checkpoint"),
    ]
    db.add_all(schedule)
    db.commit()
