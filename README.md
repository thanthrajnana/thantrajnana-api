# Thantrajnana Unified API

A single FastAPI backend containing:

- Public website authentication, course catalog, checkout and enrollments
- Student dashboard
- Teacher dashboard
- Arduino and ESP32 visual coding Studio
- Web Scratch visual coding Studio and website ZIP export

## Run locally

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

## Main route groups

- `/api/v1/auth`
- `/api/v1/courses`
- `/api/v1/catalog`
- `/api/v1/orders`
- `/api/v1/enrollments`
- `/api/v1/student`
- `/api/v1/teacher`
- `/api/v1/studio/projects` — Arduino/ESP32 projects
- `/api/v1/studio/toolchain` — boards, serial ports, compile and upload
- `/api/v1/studio/web-projects` — web Scratch projects and ZIP export

## Demo accounts

- Student: `student@thantrajnana.com` / `Student@123`
- Teacher: `teacher@thantrajnana.com` / `Teacher@123`

## PostgreSQL

The `.env.example` uses:

```env
DATABASE_URL=postgresql+psycopg://postgres:Thanthrajnana@localhost:5432/thanthrajnana
```

Generate a secret key:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## Existing database warning

This merge unifies model definitions from three previously separate APIs. SQLAlchemy `create_all()` creates missing tables but does not add missing columns to existing tables. For an existing development database, back it up and either:

1. create a new empty database for this merged API, or
2. create proper Alembic migrations before using it with production data.

A fresh empty database is recommended for the first run.
