from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBrief


class ReviewCreate(BaseModel):
    rating: float = Field(ge=0.5, le=5.0, multiple_of=0.5)
    title: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)
    is_spoiler: bool = False


class ReviewUpdate(BaseModel):
    rating: float | None = Field(default=None, ge=0.5, le=5.0, multiple_of=0.5)
    title: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    is_spoiler: bool | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    user: UserBrief
    rating: float
    title: str | None = None
    content: str
    is_spoiler: bool
    like_count: int
    comment_count: int
    report_count: int
    created_at: datetime
    updated_at: datetime
