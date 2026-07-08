from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follows_follower_following"),
        CheckConstraint("follower_id <> following_id", name="ck_follows_no_self_follow"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")
