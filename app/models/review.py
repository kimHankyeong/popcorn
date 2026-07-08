from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_reviews_user_movie"),
        CheckConstraint("rating >= 0.5 AND rating <= 5.0", name="ck_reviews_rating_range"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_spoiler: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    reports = relationship("ReviewReport", back_populates="review", cascade="all, delete-orphan")
