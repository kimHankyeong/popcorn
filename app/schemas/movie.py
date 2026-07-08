from datetime import date

from pydantic import BaseModel, ConfigDict


class MovieListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    poster_url: str | None = None
    release_date: date | None = None
    average_rating: float
    review_count: int


class MovieDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_title: str | None = None
    release_date: date | None = None
    runtime_minutes: int | None = None
    director: str | None = None
    poster_url: str | None = None
    overview: str | None = None
    genres: list[str]
    average_rating: float
    review_count: int
