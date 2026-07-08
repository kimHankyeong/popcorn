from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.user import UserMe

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise ConflictError("이미 사용 중인 이메일입니다.", error_code="EMAIL_ALREADY_EXISTS")
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise ConflictError("이미 사용 중인 아이디입니다.", error_code="USERNAME_ALREADY_EXISTS")

    user = User(
        email=payload.email,
        username=payload.username,
        nickname=payload.nickname,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("이메일 또는 비밀번호가 올바르지 않습니다.", error_code="INVALID_CREDENTIALS")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    try:
        user_id = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise UnauthorizedError(str(exc), error_code="INVALID_REFRESH_TOKEN") from exc

    if db.get(User, user_id) is None:
        raise UnauthorizedError("사용자를 찾을 수 없습니다.")

    return AccessTokenResponse(access_token=create_access_token(user_id))


@router.get("/me", response_model=UserMe)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
