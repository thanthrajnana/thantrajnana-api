import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./thantrajnana_test.db"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


TEST_DB = Path("thantrajnana_test.db")


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_student_and_teacher_workflows():
    if TEST_DB.exists():
        TEST_DB.unlink()

    with TestClient(app) as client:
        student_headers = login(client, "student@thantrajnana.com", "Student@123")
        teacher_headers = login(client, "teacher@thantrajnana.com", "Teacher@123")

        student_dashboard = client.get("/api/v1/student/dashboard", headers=student_headers)
        teacher_dashboard = client.get("/api/v1/teacher/dashboard", headers=teacher_headers)
        assert student_dashboard.status_code == 200
        assert teacher_dashboard.status_code == 200
        assert student_dashboard.json()["stats"]["active_courses"] >= 1
        assert teacher_dashboard.json()["stats"]["total_students"] >= 1

        teacher_courses = client.get("/api/v1/teacher/courses", headers=teacher_headers).json()
        course_id = teacher_courses[0]["course"]["id"]
        created = client.post(
            "/api/v1/teacher/assignments",
            headers=teacher_headers,
            json={
                "course_id": course_id,
                "title": "Test assignment",
                "description": "A complete test assignment description.",
                "due_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "max_score": 50,
            },
        )
        assert created.status_code == 201, created.text

        forbidden = client.get("/api/v1/teacher/dashboard", headers=student_headers)
        assert forbidden.status_code == 403

    if TEST_DB.exists():
        TEST_DB.unlink()
