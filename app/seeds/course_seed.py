from sqlalchemy.orm import Session

from app.models.courses.course import Course


def seed_courses(db: Session):
    existing_course = db.query(Course).first()

    if existing_course:
        return

    courses = [
        Course(
            title="Mobile App Development",
            slug="mobile-app-development",
            description="Build mobile apps using Scratch-style visual coding.",
            category="Mobile App",
            price=4999,
            duration="12 weeks",
            level="Beginner",
            has_kit=False,
            platform_type="mobile_builder",
            is_published=True,
        ),
        Course(
            title="Web Development",
            slug="web-development",
            description="Learn to build websites and web apps visually.",
            category="Web Development",
            price=4999,
            duration="12 weeks",
            level="Beginner",
            has_kit=False,
            platform_type="web_builder",
            is_published=True,
        ),
        Course(
            title="IoT with ESP32",
            slug="iot-with-esp32",
            description="Build IoT projects using ESP32 and sensors.",
            category="IoT",
            price=6999,
            duration="14 weeks",
            level="Intermediate",
            has_kit=True,
            platform_type="iot_builder",
            is_published=True,
        ),
        Course(
            title="Arduino Embedded Systems",
            slug="arduino-embedded-systems",
            description="Learn embedded systems using Arduino hardware.",
            category="Embedded Systems",
            price=5999,
            duration="12 weeks",
            level="Beginner",
            has_kit=True,
            platform_type="arduino_builder",
            is_published=True,
        ),
        Course(
            title="Robotics with Arduino",
            slug="robotics-with-arduino",
            description="Build robots using Arduino, motors, and sensors.",
            category="Robotics",
            price=7999,
            duration="16 weeks",
            level="Intermediate",
            has_kit=True,
            platform_type="robotics_builder",
            is_published=True,
        ),
    ]

    db.add_all(courses)
    db.commit()
    