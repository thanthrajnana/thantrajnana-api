from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.auth.user import User  # noqa
from app.models.role import Role  # noqa
from app.models.user_role import UserRole  # noqa
from app.models.courses.course import Course  # noqa
