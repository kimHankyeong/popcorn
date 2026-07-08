from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBrief


class ReportCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class ReviewReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    reporter: UserBrief
    reason: str | None = None
    created_at: datetime


class CommentReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comment_id: int
    reporter: UserBrief
    reason: str | None = None
    created_at: datetime


class HiddenReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    user: UserBrief
    title: str | None = None
    content: str
    report_count: int
    reports: list[ReviewReportOut]


class HiddenCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: int
    user: UserBrief
    content: str
    report_count: int
    reports: list[CommentReportOut]
