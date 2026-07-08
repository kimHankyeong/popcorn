from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.moderation import contains_profanity
from app.database import get_db
from app.models.like import ReviewLike
from app.models.movie import Movie
from app.models.report import ReviewReport
from app.models.review import Review
from app.models.user import User
from app.schemas.report import ReportCreate
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate

router = APIRouter(tags=["Reviews"])
settings = get_settings()


def _get_review_or_404(db: Session, review_id: int) -> Review:
    review = db.scalar(
        select(Review).where(Review.id == review_id, Review.deleted_at.is_(None), Review.is_hidden.is_(False))
    )
    if review is None:
        raise NotFoundError("리뷰를 찾을 수 없습니다.", error_code="REVIEW_NOT_FOUND")
    return review


def _refresh_movie_rating_cache(db: Session, movie_id: int) -> None:
    stats = db.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(
            Review.movie_id == movie_id, Review.deleted_at.is_(None)
        )
    ).one()
    review_count, average_rating = stats
    movie = db.get(Movie, movie_id)
    movie.review_count = review_count or 0
    movie.average_rating = round(float(average_rating), 2) if average_rating is not None else 0


def _assert_clean(*texts: str | None) -> None:
    for text in texts:
        if text and contains_profanity(text):
            raise BadRequestError(
                "부적절한 표현이 포함되어 있어 등록할 수 없습니다.", error_code="PROFANITY_DETECTED"
            )


@router.get("/reviews/hot", response_model=list[ReviewOut])
def get_hot_reviews(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[Review]:
    """영화 종류와 무관하게 반응(좋아요+댓글)이 많은 인기 토론방 요약."""
    score = (Review.like_count + Review.comment_count).label("score")
    stmt = (
        select(Review)
        .where(Review.deleted_at.is_(None), Review.is_hidden.is_(False))
        .order_by(score.desc(), Review.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@router.post("/movies/{movie_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    movie_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Review:
    if db.get(Movie, movie_id) is None:
        raise NotFoundError("영화를 찾을 수 없습니다.", error_code="MOVIE_NOT_FOUND")

    existing = db.scalar(
        select(Review).where(
            Review.movie_id == movie_id, Review.user_id == current_user.id, Review.deleted_at.is_(None)
        )
    )
    if existing is not None:
        raise ConflictError("이미 이 영화에 리뷰를 작성했습니다.", error_code="REVIEW_ALREADY_EXISTS")

    _assert_clean(payload.title, payload.content)

    review = Review(
        movie_id=movie_id,
        user_id=current_user.id,
        rating=payload.rating,
        title=payload.title,
        content=payload.content,
        is_spoiler=payload.is_spoiler,
    )
    db.add(review)
    db.flush()
    _refresh_movie_rating_cache(db, movie_id)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)) -> Review:
    return _get_review_or_404(db, review_id)


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Review:
    review = _get_review_or_404(db, review_id)
    if review.user_id != current_user.id:
        raise ForbiddenError("본인의 리뷰만 수정할 수 있습니다.")

    _assert_clean(payload.title, payload.content)

    rating_changed = payload.rating is not None and payload.rating != review.rating
    if payload.rating is not None:
        review.rating = payload.rating
    if payload.title is not None:
        review.title = payload.title
    if payload.content is not None:
        review.content = payload.content
    if payload.is_spoiler is not None:
        review.is_spoiler = payload.is_spoiler

    if rating_changed:
        db.flush()
        _refresh_movie_rating_cache(db, review.movie_id)

    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    review = _get_review_or_404(db, review_id)
    if review.user_id != current_user.id:
        raise ForbiddenError("본인의 리뷰만 삭제할 수 있습니다.")

    review.deleted_at = datetime.now(timezone.utc)
    db.flush()
    _refresh_movie_rating_cache(db, review.movie_id)
    db.commit()


@router.post("/reviews/{review_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    review = _get_review_or_404(db, review_id)

    existing = db.scalar(
        select(ReviewLike).where(ReviewLike.user_id == current_user.id, ReviewLike.review_id == review_id)
    )
    if existing is not None:
        raise ConflictError("이미 좋아요를 눌렀습니다.", error_code="ALREADY_LIKED")

    db.add(ReviewLike(user_id=current_user.id, review_id=review_id))
    review.like_count += 1
    db.commit()


@router.delete("/reviews/{review_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    review = _get_review_or_404(db, review_id)

    like = db.scalar(
        select(ReviewLike).where(ReviewLike.user_id == current_user.id, ReviewLike.review_id == review_id)
    )
    if like is None:
        raise NotFoundError("좋아요 기록을 찾을 수 없습니다.", error_code="LIKE_NOT_FOUND")

    db.delete(like)
    review.like_count = max(0, review.like_count - 1)
    db.commit()


@router.post("/reviews/{review_id}/reports", status_code=status.HTTP_204_NO_CONTENT)
def report_review(
    review_id: int,
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    review = _get_review_or_404(db, review_id)
    if review.user_id == current_user.id:
        raise BadRequestError("본인의 리뷰는 신고할 수 없습니다.", error_code="SELF_REPORT_NOT_ALLOWED")

    existing = db.scalar(
        select(ReviewReport).where(ReviewReport.reporter_id == current_user.id, ReviewReport.review_id == review_id)
    )
    if existing is not None:
        raise ConflictError("이미 신고한 리뷰입니다.", error_code="ALREADY_REPORTED")

    db.add(ReviewReport(reporter_id=current_user.id, review_id=review_id, reason=payload.reason))
    review.report_count += 1
    if review.report_count >= settings.report_hide_threshold:
        review.is_hidden = True
    db.commit()
