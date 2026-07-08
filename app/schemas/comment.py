from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBrief


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    parent_comment_id: int | None = None
    is_spoiler: bool = False


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1)
    is_spoiler: bool | None = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserBrief
    content: str
    is_spoiler: bool
    like_count: int
    created_at: datetime


class CommentWithReplies(CommentOut):
    replies: list[CommentOut] = []


class CommentListResponse(BaseModel):
    items: list[CommentWithReplies]
    total: int
