from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.common import router as common_router
from app.api.commerce import router as commerce_router
from app.api.courses import router as courses_router
from app.api.student import router as student_router
from app.api.teacher import router as teacher_router
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.seeds.seed import seed_database
from app.studio.routers.projects import router as hardware_projects_router
from app.studio.routers.toolchain import router as studio_toolchain_router
from app.web_studio.routers.projects import router as web_projects_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Unified Thantrajnana website, student dashboard, teacher dashboard, Arduino/ESP32 studio and web Scratch studio API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": [
                {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
                for error in exc.errors()
            ],
        },
    )


app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(common_router, prefix=settings.api_prefix)
app.include_router(courses_router, prefix=settings.api_prefix)
app.include_router(commerce_router, prefix=settings.api_prefix)
app.include_router(student_router, prefix=settings.api_prefix)
app.include_router(teacher_router, prefix=settings.api_prefix)
app.include_router(hardware_projects_router, prefix=f"{settings.api_prefix}/studio")
app.include_router(studio_toolchain_router, prefix=f"{settings.api_prefix}/studio")
app.include_router(web_projects_router, prefix=f"{settings.api_prefix}/studio")


@app.get("/")
def root():
    return {
        "message": "Thantrajnana Unified API is running",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
        "modules": ["website", "student-dashboard", "teacher-dashboard", "hardware-studio", "web-studio"],
    }


@app.get("/health")
@app.get("/api/v1/health", include_in_schema=False)
def health():
    return {"status": "healthy", "service": settings.app_name}
