from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.database import get_db
from app.models.follow import Follow
from app.models.review import Review
from app.models.user import User
from app.schemas.common import PaginatedResponse, Pagination, pagination_params
from app.schemas.review import ReviewOut
from app.schemas.user import UserMe, UserMeUpdate, UserPublic

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_or_404(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise NotFoundError("사용자를 찾을 수 없습니다.", error_code="USER_NOT_FOUND")
    return user


def _to_user_public(db: Session, user: User) -> UserPublic:
    follower_count = db.scalar(select(func.count()).select_from(Follow).where(Follow.following_id == user.id)) or 0
    following_count = db.scalar(select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)) or 0
    return UserPublic(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        profile_image_url=user.profile_image_url,
        bio=user.bio,
        follower_count=follower_count,
        following_count=following_count,
    )


@router.get("/{username}", response_model=UserPublic)
def get_user_profile(username: str, db: Session = Depends(get_db)) -> UserPublic:
    user = _get_user_or_404(db, username)
    return _to_user_public(db, user)


@router.patch("/me", response_model=UserMe)
def update_me(
    payload: UserMeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if payload.nickname is not None:
        current_user.nickname = payload.nickname
    if payload.bio is not None:
        current_user.bio = payload.bio
    if payload.profile_image_url is not None:
        current_user.profile_image_url = payload.profile_image_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}/reviews", response_model=PaginatedResponse[ReviewOut])
def get_user_reviews(
    username: str,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReviewOut]:
    user = _get_user_or_404(db, username)

    base_query = select(Review).where(Review.user_id == user.id, Review.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    reviews = db.scalars(
        base_query.order_by(Review.created_at.desc()).offset(pagination.skip).limit(pagination.limit)
    ).all()

    return PaginatedResponse[ReviewOut](items=[ReviewOut.model_validate(r) for r in reviews], total=total)


@router.post("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    target = _get_user_or_404(db, username)
    if target.id == current_user.id:
        raise BadRequestError("자기 자신을 팔로우할 수 없습니다.", error_code="SELF_FOLLOW_NOT_ALLOWED")

    existing = db.scalar(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target.id)
    )
    if existing is not None:
        raise ConflictError("이미 팔로우한 사용자입니다.", error_code="ALREADY_FOLLOWING")

    db.add(Follow(follower_id=current_user.id, following_id=target.id))
    db.commit()


@router.delete("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    target = _get_user_or_404(db, username)
    follow = db.scalar(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target.id)
    )
    if follow is None:
        raise NotFoundError("팔로우 관계를 찾을 수 없습니다.", error_code="FOLLOW_NOT_FOUND")

    db.delete(follow)
    db.commit()


@router.get("/{username}/followers", response_model=PaginatedResponse[UserPublic])
def get_followers(
    username: str,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserPublic]:
    user = _get_user_or_404(db, username)

    query = select(User).join(Follow, Follow.follower_id == User.id).where(Follow.following_id == user.id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    followers = db.scalars(query.offset(pagination.skip).limit(pagination.limit)).all()

    return PaginatedResponse[UserPublic](items=[_to_user_public(db, u) for u in followers], total=total)


@router.get("/{username}/following", response_model=PaginatedResponse[UserPublic])
def get_following(
    username: str,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserPublic]:
    user = _get_user_or_404(db, username)

    query = select(User).join(Follow, Follow.following_id == User.id).where(Follow.follower_id == user.id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    following = db.scalars(query.offset(pagination.skip).limit(pagination.limit)).all()

    return PaginatedResponse[UserPublic](items=[_to_user_public(db, u) for u in following], total=total)
