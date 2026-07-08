from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_spoiler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    review = relationship("Review", back_populates="comments")
    user = relationship("User", back_populates="comments")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    reports = relationship("CommentReport", back_populates="comment", cascade="all, delete-orphan")

    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
