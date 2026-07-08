from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# SQLite는 BIGINT 기본키를 rowid alias로 취급하지 않아 autoincrement가 동작하지 않는다.
# PostgreSQL에서는 BIGSERIAL(BigInteger)로, SQLite에서는 INTEGER(rowid alias)로 매핑한다.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
