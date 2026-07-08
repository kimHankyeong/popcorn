from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class ReviewReport(Base):
    __tablename__ = "review_reports"
    __table_args__ = (UniqueConstraint("reporter_id", "review_id", name="uq_review_reports_reporter_review"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reporter = relationship("User")
    review = relationship("Review", back_populates="reports")


class CommentReport(Base):
    __tablename__ = "comment_reports"
    __table_args__ = (UniqueConstraint("reporter_id", "comment_id", name="uq_comment_reports_reporter_comment"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reporter = relationship("User")
    comment = relationship("Comment", back_populates="reports")
