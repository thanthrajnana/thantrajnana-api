from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# ----------------------------
# Register Request
# ----------------------------
class UserRegister(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None
    password: str


# ----------------------------
# Login Request
# ----------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ----------------------------
# User Response
# ----------------------------
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None
    profile_image_url: str | None = None
    email_verified: bool
    phone_verified: bool
    status: str


# ----------------------------
# JWT Token Response
# ----------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    