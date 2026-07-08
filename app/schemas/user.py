from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBrief(BaseModel):
    """리뷰/댓글에 함께 담기는 최소 사용자 정보."""

    model_config = ConfigDict(from_attributes=True)

    username: str
    nickname: str
    profile_image_url: str | None = None


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: str
    profile_image_url: str | None = None
    bio: str | None = None
    follower_count: int
    following_count: int


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    nickname: str
    profile_image_url: str | None = None
    bio: str | None = None
    created_at: datetime


class UserMeUpdate(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    bio: str | None = None
    profile_image_url: str | None = Field(default=None, max_length=500)
