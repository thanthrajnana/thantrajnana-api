from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserLogin, UserPublic, UserRegister


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Email is already registered")
    if payload.phone and db.scalar(select(User).where(User.phone == payload.phone)):
        raise HTTPException(status_code=400, detail="Phone number is already registered")
    initials = (payload.first_name[:1] + (payload.last_name or "")[:1]).upper() or "TJ"
    user = User(
        first_name=payload.first_name.strip(),
        last_name=(payload.last_name or "").strip(),
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="STUDENT",
        avatar_initials=initials,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, role=user.role, extra={"email": user.email})
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token = create_access_token(
        subject=user.id,
        role=user.role,
        extra={"email": user.email},
    )
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
