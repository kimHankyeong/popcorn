from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_admin
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.comment import Comment
from app.models.review import Review
from app.models.user import User
from app.schemas.report import HiddenCommentOut, HiddenReviewOut

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/reports/reviews",
    response_model=list[HiddenReviewOut],
    dependencies=[Depends(require_admin)],
)
def list_hidden_reviews(db: Session = Depends(get_db)) -> list[Review]:
    """신고 누적으로 자동 숨김된 리뷰(관리자 검토 대기열)."""
    stmt = (
        select(Review)
        .where(Review.is_hidden.is_(True), Review.deleted_at.is_(None))
        .options(selectinload(Review.reports))
        .order_by(Review.report_count.desc())
    )
    return list(db.scalars(stmt).all())


@router.get(
    "/reports/comments",
    response_model=list[HiddenCommentOut],
    dependencies=[Depends(require_admin)],
)
def list_hidden_comments(db: Session = Depends(get_db)) -> list[Comment]:
    """신고 누적으로 자동 숨김된 댓글(관리자 검토 대기열)."""
    stmt = (
        select(Comment)
        .where(Comment.is_hidden.is_(True), Comment.deleted_at.is_(None))
        .options(selectinload(Comment.reports))
        .order_by(Comment.report_count.desc())
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/reviews/{review_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def restore_review(review_id: int, db: Session = Depends(get_db)) -> None:
    """검토 결과 문제가 없다고 판단되면 숨김을 해제한다."""
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError("리뷰를 찾을 수 없습니다.", error_code="REVIEW_NOT_FOUND")
    review.is_hidden = False
    db.commit()


@router.post(
    "/reviews/{review_id}/remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def remove_review(review_id: int, db: Session = Depends(get_db)) -> None:
    """검토 결과 부적절하다고 판단되면 소프트 삭제한다."""
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError("리뷰를 찾을 수 없습니다.", error_code="REVIEW_NOT_FOUND")
    review.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post(
    "/comments/{comment_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def restore_comment(comment_id: int, db: Session = Depends(get_db)) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise NotFoundError("댓글을 찾을 수 없습니다.", error_code="COMMENT_NOT_FOUND")
    comment.is_hidden = False
    db.commit()


@router.post(
    "/comments/{comment_id}/remove",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def remove_comment(comment_id: int, db: Session = Depends(get_db)) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise NotFoundError("댓글을 찾을 수 없습니다.", error_code="COMMENT_NOT_FOUND")
    comment.deleted_at = datetime.now(timezone.utc)
    db.commit()
