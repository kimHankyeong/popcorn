from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.genre import Genre
from app.schemas.genre import GenreOut

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)) -> list[Genre]:
    return list(db.scalars(select(Genre).order_by(Genre.name)).all())
