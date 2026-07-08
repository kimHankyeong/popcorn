"""초기 장르/영화 샘플 데이터를 DB에 채워 넣는 스크립트.

실행: venv/Scripts/python.exe seed_data.py
"""

from datetime import date

from sqlalchemy import select

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.genre import Genre
from app.models.movie import Movie
from app.models.user import User

ADMIN_EMAIL = "admin@popback.com"
ADMIN_PASSWORD = "admin1234"

GENRES = ["액션", "드라마", "코미디", "SF", "스릴러", "로맨스", "애니메이션", "공포", "판타지", "다큐멘터리"]

MOVIES = [
    {
        "title": "인터스텔라",
        "original_title": "Interstellar",
        "release_date": date(2014, 11, 6),
        "runtime_minutes": 169,
        "director": "크리스토퍼 놀란",
        "poster_url": "https://image.tmdb.org/t/p/w500/nBNZadXqJSdt05SHLqgT0HuC5Gm.jpg",
        "overview": "인류의 새로운 터전을 찾기 위해 우주로 떠나는 탐사대의 이야기.",
        "genres": ["SF", "드라마"],
    },
    {
        "title": "기생충",
        "original_title": "Parasite",
        "release_date": date(2019, 5, 30),
        "runtime_minutes": 132,
        "director": "봉준호",
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "overview": "전원 백수인 기택 가족이 부잣집에 취업하며 벌어지는 이야기.",
        "genres": ["드라마", "스릴러"],
    },
    {
        "title": "라라랜드",
        "original_title": "La La Land",
        "release_date": date(2016, 12, 7),
        "runtime_minutes": 128,
        "director": "데이미언 셔젤",
        "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
        "overview": "재즈 피아니스트와 배우 지망생의 사랑과 꿈에 관한 이야기.",
        "genres": ["로맨스", "드라마"],
    },
    {
        "title": "어벤져스: 엔드게임",
        "original_title": "Avengers: Endgame",
        "release_date": date(2019, 4, 24),
        "runtime_minutes": 181,
        "director": "안소니 루소, 조 루소",
        "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "overview": "타노스에게 패배한 어벤져스가 마지막 희망을 걸고 다시 모인다.",
        "genres": ["액션", "SF"],
    },
    {
        "title": "너의 이름은.",
        "original_title": "君の名は。",
        "release_date": date(2016, 8, 26),
        "runtime_minutes": 106,
        "director": "신카이 마코토",
        "poster_url": "https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg",
        "overview": "몸이 뒤바뀐 두 소년 소녀의 운명적인 이야기.",
        "genres": ["애니메이션", "로맨스", "판타지"],
    },
    {
        "title": "겟 아웃",
        "original_title": "Get Out",
        "release_date": date(2017, 2, 24),
        "runtime_minutes": 104,
        "director": "조던 필",
        "poster_url": "https://image.tmdb.org/t/p/w500/1SwBrKAtqM4B0e9U0LmveGrLoiV.jpg",
        "overview": "여자친구의 부모님 댁을 방문한 청년이 겪는 기묘하고 소름 끼치는 사건들.",
        "genres": ["공포", "스릴러"],
    },
    {
        "title": "극한직업",
        "original_title": "Extreme Job",
        "release_date": date(2019, 1, 23),
        "runtime_minutes": 111,
        "director": "이병헌",
        "poster_url": "https://image.tmdb.org/t/p/w500/eSg2VoOfB8g0aXR6ehJ9SArKIz9.jpg",
        "overview": "치킨집으로 위장한 마약반 형사들의 잠복수사 코미디.",
        "genres": ["코미디", "액션"],
    },
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        genre_by_name: dict[str, Genre] = {}
        for name in GENRES:
            genre = db.scalar(select(Genre).where(Genre.name == name))
            if genre is None:
                genre = Genre(name=name)
                db.add(genre)
                db.flush()
            genre_by_name[name] = genre

        for movie_data in MOVIES:
            existing = db.scalar(select(Movie).where(Movie.title == movie_data["title"]))
            if existing is not None:
                continue

            movie = Movie(
                title=movie_data["title"],
                original_title=movie_data["original_title"],
                release_date=movie_data["release_date"],
                runtime_minutes=movie_data["runtime_minutes"],
                director=movie_data["director"],
                poster_url=movie_data["poster_url"],
                overview=movie_data["overview"],
            )
            movie.genres = [genre_by_name[name] for name in movie_data["genres"]]
            db.add(movie)

        admin = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if admin is None:
            admin = User(
                email=ADMIN_EMAIL,
                username="admin",
                nickname="관리자",
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin)

        db.commit()
        print(f"완료: 장르 {len(GENRES)}개, 영화 {len(MOVIES)}개 확인/추가, 관리자 계정({ADMIN_EMAIL}/{ADMIN_PASSWORD}) 확인/추가")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
