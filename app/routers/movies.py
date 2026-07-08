from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.genre import Genre
from app.models.movie import Movie
from app.models.review import Review
from app.schemas.common import PaginatedResponse, Pagination, pagination_params
from app.schemas.movie import MovieDetail, MovieListItem
from app.schemas.review import ReviewOut

router = APIRouter(prefix="/movies", tags=["Movies"])


def _get_movie_or_404(db: Session, movie_id: int) -> Movie:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise NotFoundError("영화를 찾을 수 없습니다.", error_code="MOVIE_NOT_FOUND")
    return movie


@router.get("", response_model=PaginatedResponse[MovieListItem])
def list_movies(
    query: str | None = Query(default=None, description="제목 검색어"),
    genre: str | None = Query(default=None, description="장르 이름으로 필터"),
    sort: Literal["rating", "recent"] = Query(default="recent"),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[MovieListItem]:
    stmt = select(Movie)

    if query:
        stmt = stmt.where(Movie.title.ilike(f"%{query}%"))
    if genre:
        stmt = stmt.join(Movie.genres).where(Genre.name == genre)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "rating":
        stmt = stmt.order_by(Movie.average_rating.desc())
    else:
        stmt = stmt.order_by(Movie.release_date.desc().nulls_last(), Movie.created_at.desc())

    movies = db.scalars(stmt.offset(pagination.skip).limit(pagination.limit)).all()
    return PaginatedResponse[MovieListItem](items=[MovieListItem.model_validate(m) for m in movies], total=total)


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieDetail:
    movie = _get_movie_or_404(db, movie_id)
    return MovieDetail(
        id=movie.id,
        title=movie.title,
        original_title=movie.original_title,
        release_date=movie.release_date,
        runtime_minutes=movie.runtime_minutes,
        director=movie.director,
        poster_url=movie.poster_url,
        overview=movie.overview,
        genres=[g.name for g in movie.genres],
        average_rating=movie.average_rating,
        review_count=movie.review_count,
    )


@router.get("/{movie_id}/reviews", response_model=PaginatedResponse[ReviewOut])
def get_movie_reviews(
    movie_id: int,
    sort: Literal["likes", "recent"] = Query(default="recent"),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReviewOut]:
    _get_movie_or_404(db, movie_id)

    stmt = select(Review).where(Review.movie_id == movie_id, Review.deleted_at.is_(None))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "likes":
        stmt = stmt.order_by(Review.like_count.desc(), Review.created_at.desc())
    else:
        stmt = stmt.order_by(Review.created_at.desc())

    reviews = db.scalars(stmt.offset(pagination.skip).limit(pagination.limit)).all()
    return PaginatedResponse[ReviewOut](items=[ReviewOut.model_validate(r) for r in reviews], total=total)
