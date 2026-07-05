from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.auth import router as auth_router
from app.core.security import get_current_user
from app.db.database import Base, engine
from app.models.auth.user import User
from app.schemas.user import UserResponse
from app.api.courses.course_router import router as course_router

from app.db.database import SessionLocal
from app.seeds.course_seed import seed_courses


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_courses(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="Thantrajnana API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "Thantrajnana API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

app.include_router(course_router)
    