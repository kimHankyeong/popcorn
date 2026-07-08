from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class ReviewLike(Base):
    __tablename__ = "review_likes"
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="uq_review_likes_user_review"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="review_likes")
    review = relationship("Review", back_populates="likes")


class CommentLike(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uq_comment_likes_user_comment"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="comment_likes")
    comment = relationship("Comment", back_populates="likes")
