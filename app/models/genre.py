from sqlalchemy import BigInteger, ForeignKey, Integer, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies = relationship("Movie", secondary=movie_genres, back_populates="genres")
