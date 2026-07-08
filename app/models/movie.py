from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, BigIntPK
from app.models.genre import movie_genres


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    director: Mapped[str | None] = mapped_column(String(255), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 비정규화 캐시 컬럼: 리뷰 생성/삭제 시 애플리케이션 레벨에서 갱신
    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    genres = relationship("Genre", secondary=movie_genres, back_populates="movies")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
