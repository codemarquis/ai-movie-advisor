"""
Thin TMDB client for live catalogue data (popular, search, genres).

Not yet used by the UI (see README roadmap). It has no Streamlit dependency;
callers decide how to cache and how to show errors.
"""
import logging

from tmdbv3api import Discover, Movie, TMDb

from config import tmdb_api_key

log = logging.getLogger(__name__)

IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDBService:
    def __init__(self) -> None:
        key = tmdb_api_key()
        if not key:
            raise RuntimeError("TMDB_API_KEY is not set")
        TMDb().api_key = key
        self._movie = Movie()
        self._discover = Discover()

    def popular_movies(self, page: int = 1) -> list[dict]:
        return [self._format(m) for m in self._movie.popular(page=page)]

    def search_movies(self, query: str) -> list[dict]:
        return [self._format(m) for m in self._movie.search(query[:100])]

    def movies_by_genre(self, genre_id: int, page: int = 1) -> list[dict]:
        return [self._format(m) for m in self._discover.discover_movies({"with_genres": genre_id, "page": page})]

    def genres(self) -> list[dict]:
        return [{"id": g.id, "name": g.name} for g in self._movie.genres()]

    @staticmethod
    def _format(movie) -> dict:
        release = getattr(movie, "release_date", "") or ""
        poster = getattr(movie, "poster_path", None)
        return {
            "id": movie.id,
            "title": movie.title,
            "genre_ids": getattr(movie, "genre_ids", []),
            "year": int(release[:4]) if release[:4].isdigit() else None,
            "rating": getattr(movie, "vote_average", 0.0),
            "votes": getattr(movie, "vote_count", 0),
            "poster_url": f"{IMAGE_BASE}{poster}" if isinstance(poster, str) and poster.startswith("/") else None,
            "overview": getattr(movie, "overview", ""),
        }
