from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel):
    skip: int = 0
    limit: int = 20


def pagination_params(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)) -> Pagination:
    return Pagination(skip=skip, limit=limit)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
