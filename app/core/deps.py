from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import TokenError, decode_token
from app.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("인증 토큰이 필요합니다.")

    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("사용자를 찾을 수 없습니다.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise ForbiddenError("관리자만 접근할 수 있습니다.", error_code="ADMIN_ONLY")
    return current_user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError:
        return None
    return db.get(User, user_id)
