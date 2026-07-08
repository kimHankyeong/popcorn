from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    review_likes = relationship("ReviewLike", back_populates="user", cascade="all, delete-orphan")
    comment_likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")

    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
    followers = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan",
    )
