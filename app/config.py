from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """앱 전역 설정. 환경변수 또는 .env 파일에서 값을 읽는다.

    DB 설계(db_design.md)는 PostgreSQL을 기준으로 작성되었으나, 로컬에 PostgreSQL이
    설치되어 있지 않은 개발 환경에서도 바로 실행할 수 있도록 기본값은 SQLite 파일로
    둔다. 운영 환경에서는 DATABASE_URL을 postgresql+psycopg2://... 형태로 지정하면
    코드 변경 없이 그대로 PostgreSQL을 사용할 수 있다.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Popback API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./popback.db"

    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # 리뷰/댓글이 이 횟수 이상 신고되면 자동으로 숨김 처리되고 관리자 검토 대기열로 들어간다.
    report_hide_threshold: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
