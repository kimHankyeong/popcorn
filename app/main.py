from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.database import Base, engine
from app.models import *  # noqa: F401,F403  # 모든 모델을 Base.metadata에 등록하기 위해 임포트
from app.routers import admin, auth, comments, genres, movies, reviews, users

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

api_router_prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=api_router_prefix)
app.include_router(users.router, prefix=api_router_prefix)
app.include_router(movies.router, prefix=api_router_prefix)
app.include_router(genres.router, prefix=api_router_prefix)
app.include_router(reviews.router, prefix=api_router_prefix)
app.include_router(comments.router, prefix=api_router_prefix)
app.include_router(admin.router, prefix=api_router_prefix)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
