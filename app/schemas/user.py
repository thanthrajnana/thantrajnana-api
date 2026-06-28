from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None
    password: str


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str | None
    email: EmailStr
    phone: str | None
    status: str

    class Config:
        from_attributes = True