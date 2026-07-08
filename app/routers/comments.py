from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.core.deps import get_current_user
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.moderation import contains_profanity
from app.database import get_db
from app.models.comment import Comment
from app.models.like import CommentLike
from app.models.report import CommentReport
from app.models.review import Review
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentListResponse, CommentOut, CommentUpdate, CommentWithReplies
from app.schemas.common import Pagination, pagination_params
from app.schemas.report import ReportCreate

router = APIRouter(tags=["Comments"])
settings = get_settings()


def _get_review_or_404(db: Session, review_id: int) -> Review:
    review = db.scalar(
        select(Review).where(Review.id == review_id, Review.deleted_at.is_(None), Review.is_hidden.is_(False))
    )
    if review is None:
        raise NotFoundError("리뷰를 찾을 수 없습니다.", error_code="REVIEW_NOT_FOUND")
    return review


def _get_comment_or_404(db: Session, comment_id: int) -> Comment:
    comment = db.scalar(
        select(Comment).where(
            Comment.id == comment_id, Comment.deleted_at.is_(None), Comment.is_hidden.is_(False)
        )
    )
    if comment is None:
        raise NotFoundError("댓글을 찾을 수 없습니다.", error_code="COMMENT_NOT_FOUND")
    return comment


def _refresh_review_comment_count(db: Session, review_id: int) -> None:
    count = db.scalar(
        select(func.count()).where(Comment.review_id == review_id, Comment.deleted_at.is_(None))
    ) or 0
    review = db.get(Review, review_id)
    review.comment_count = count


@router.get("/reviews/{review_id}/comments", response_model=CommentListResponse)
def list_comments(
    review_id: int,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> CommentListResponse:
    _get_review_or_404(db, review_id)

    top_level_stmt = select(Comment).where(
        Comment.review_id == review_id,
        Comment.parent_comment_id.is_(None),
        Comment.deleted_at.is_(None),
        Comment.is_hidden.is_(False),
    )
    total = db.scalar(select(func.count()).select_from(top_level_stmt.subquery())) or 0

    top_level_comments = db.scalars(
        top_level_stmt.options(selectinload(Comment.replies))
        .order_by(Comment.created_at.asc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()

    items = []
    for comment in top_level_comments:
        replies = [r for r in comment.replies if r.deleted_at is None and not r.is_hidden]
        replies.sort(key=lambda r: r.created_at)
        items.append(
            CommentWithReplies(
                **CommentOut.model_validate(comment).model_dump(),
                replies=[CommentOut.model_validate(r) for r in replies],
            )
        )

    return CommentListResponse(items=items, total=total)


@router.post("/reviews/{review_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    review_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    _get_review_or_404(db, review_id)

    if payload.parent_comment_id is not None:
        parent = db.scalar(
            select(Comment).where(
                Comment.id == payload.parent_comment_id,
                Comment.review_id == review_id,
                Comment.deleted_at.is_(None),
            )
        )
        if parent is None:
            raise NotFoundError("답글을 달 댓글을 찾을 수 없습니다.", error_code="PARENT_COMMENT_NOT_FOUND")
        if parent.parent_comment_id is not None:
            raise BadRequestError("대댓글에는 답글을 달 수 없습니다.", error_code="REPLY_DEPTH_EXCEEDED")

    if contains_profanity(payload.content):
        raise BadRequestError(
            "부적절한 표현이 포함되어 있어 등록할 수 없습니다.", error_code="PROFANITY_DETECTED"
        )

    comment = Comment(
        review_id=review_id,
        user_id=current_user.id,
        parent_comment_id=payload.parent_comment_id,
        content=payload.content,
        is_spoiler=payload.is_spoiler,
    )
    db.add(comment)
    db.flush()
    _refresh_review_comment_count(db, review_id)
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    comment = _get_comment_or_404(db, comment_id)
    if comment.user_id != current_user.id:
        raise ForbiddenError("본인의 댓글만 수정할 수 있습니다.")

    if contains_profanity(payload.content):
        raise BadRequestError(
            "부적절한 표현이 포함되어 있어 등록할 수 없습니다.", error_code="PROFANITY_DETECTED"
        )

    comment.content = payload.content
    if payload.is_spoiler is not None:
        comment.is_spoiler = payload.is_spoiler
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comment = _get_comment_or_404(db, comment_id)
    if comment.user_id != current_user.id:
        raise ForbiddenError("본인의 댓글만 삭제할 수 있습니다.")

    comment.deleted_at = datetime.now(timezone.utc)
    db.flush()
    _refresh_review_comment_count(db, comment.review_id)
    db.commit()


@router.post("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comment = _get_comment_or_404(db, comment_id)

    existing = db.scalar(
        select(CommentLike).where(CommentLike.user_id == current_user.id, CommentLike.comment_id == comment_id)
    )
    if existing is not None:
        raise ConflictError("이미 좋아요를 눌렀습니다.", error_code="ALREADY_LIKED")

    db.add(CommentLike(user_id=current_user.id, comment_id=comment_id))
    comment.like_count += 1
    db.commit()


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comment = _get_comment_or_404(db, comment_id)

    like = db.scalar(
        select(CommentLike).where(CommentLike.user_id == current_user.id, CommentLike.comment_id == comment_id)
    )
    if like is None:
        raise NotFoundError("좋아요 기록을 찾을 수 없습니다.", error_code="LIKE_NOT_FOUND")

    db.delete(like)
    comment.like_count = max(0, comment.like_count - 1)
    db.commit()


@router.post("/comments/{comment_id}/reports", status_code=status.HTTP_204_NO_CONTENT)
def report_comment(
    comment_id: int,
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comment = _get_comment_or_404(db, comment_id)
    if comment.user_id == current_user.id:
        raise BadRequestError("본인의 댓글은 신고할 수 없습니다.", error_code="SELF_REPORT_NOT_ALLOWED")

    existing = db.scalar(
        select(CommentReport).where(
            CommentReport.reporter_id == current_user.id, CommentReport.comment_id == comment_id
        )
    )
    if existing is not None:
        raise ConflictError("이미 신고한 댓글입니다.", error_code="ALREADY_REPORTED")

    db.add(CommentReport(reporter_id=current_user.id, comment_id=comment_id, reason=payload.reason))
    comment.report_count += 1
    if comment.report_count >= settings.report_hide_threshold:
        comment.is_hidden = True
    db.commit()
