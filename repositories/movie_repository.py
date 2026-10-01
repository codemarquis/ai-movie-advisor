"""
All database queries live here. Callers get plain domain objects back,
never ORM rows or sessions, so the UI and services stay database-agnostic.
"""
from collections.abc import Callable, Iterable

import pandas as pd
from sqlalchemy import func, select

from models.database import MovieRow, RatingRow, session_scope
from models.domain import Movie, MovieFilters, RatingStats
from services.mood import genres_matching

MAX_SEARCH_LENGTH = 100


def _to_movie(row: MovieRow) -> Movie:
    return Movie(
        id=row.id,
        title=row.title,
        genre=row.genre,
        year=row.year,
        rating=float(row.rating or 0.0),
        votes=int(row.votes or 0),
        poster_url=row.poster_url,
    )


def escape_like(term: str) -> str:
    """Make user input match literally inside LIKE/ILIKE: no % or _ wildcards."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---- reads (web app, read-only connection) ---------------------------------

def list_genres() -> list[str]:
    with session_scope() as session:
        return sorted(genre for (genre,) in session.execute(select(MovieRow.genre).distinct()))


def year_bounds() -> tuple[int, int]:
    with session_scope() as session:
        low, high = session.execute(select(func.min(MovieRow.year), func.max(MovieRow.year))).one()
    return (low or 1900, high or 2100)


def find_movies(filters: MovieFilters) -> list[Movie]:
    stmt = select(MovieRow).where(
        MovieRow.year.between(*filters.year_range),
        MovieRow.rating >= filters.min_rating,
    )
    if filters.genres or filters.match_mood:
        genres = set(filters.genres) or None
        if filters.match_mood:
            allowed = genres_matching(filters.mood, filters.pace)
            genres = allowed if genres is None else genres & allowed
        if not genres:
            return []
        stmt = stmt.where(MovieRow.genre.in_(sorted(genres)))
    with session_scope() as session:
        rows = session.scalars(stmt.order_by(MovieRow.rating.desc(), MovieRow.title)).all()
        return [_to_movie(r) for r in rows]


def search_movies(term: str) -> list[Movie]:
    term = (term or "").strip()[:MAX_SEARCH_LENGTH]
    if not term:
        return []
    pattern = f"%{escape_like(term)}%"
    with session_scope() as session:
        rows = session.scalars(
            select(MovieRow).where(MovieRow.title.ilike(pattern, escape="\\")).order_by(MovieRow.title)
        ).all()
        return [_to_movie(r) for r in rows]


def get_movies(ids: Iterable[int]) -> list[Movie]:
    """Movies for the given ids, in the same order (unknown ids are skipped)."""
    ids = list(ids)
    if not ids:
        return []
    with session_scope() as session:
        rows = {r.id: r for r in session.scalars(select(MovieRow).where(MovieRow.id.in_(ids)))}
        return [_to_movie(rows[i]) for i in ids if i in rows]


def top_rated_in_genre(genre: str, limit: int = 5) -> list[Movie]:
    with session_scope() as session:
        rows = session.scalars(
            select(MovieRow).where(MovieRow.genre == genre).order_by(MovieRow.rating.desc()).limit(limit)
        ).all()
        return [_to_movie(r) for r in rows]


def rating_stats(movie_id: int) -> RatingStats:
    with session_scope() as session:
        average, count = session.execute(
            select(func.avg(RatingRow.rating), func.count(RatingRow.id)).where(RatingRow.movie_id == movie_id)
        ).one()
    return RatingStats(average=float(average) if average is not None else None, count=int(count))


def ratings_frame() -> pd.DataFrame:
    """All ratings as a DataFrame with columns user_id, movie_id, rating."""
    with session_scope() as session:
        rows = session.execute(select(RatingRow.user_id, RatingRow.movie_id, RatingRow.rating)).all()
    return pd.DataFrame(rows, columns=["user_id", "movie_id", "rating"])


# ---- writes (admin scripts only, ADMIN_DATABASE_URL) -----------------------

def movie_count() -> int:
    with session_scope(read_only=False) as session:
        return session.scalar(select(func.count(MovieRow.id))) or 0


def insert_catalog(movies: list[dict], ratings: list[dict]) -> None:
    """Insert movies and their ratings in one transaction."""
    with session_scope(read_only=False) as session:
        session.add_all(MovieRow(**m) for m in movies)
        session.flush()  # movies must exist before ratings reference them
        session.add_all(RatingRow(**r) for r in ratings)


def update_poster_urls(resolve: Callable[[str, int], str]) -> int:
    """Re-resolve every movie's poster URL. Returns the number of movies updated."""
    with session_scope(read_only=False) as session:
        movies = session.scalars(select(MovieRow)).all()
        for movie in movies:
            movie.poster_url = resolve(movie.title, movie.year)
        return len(movies)
