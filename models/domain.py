"""Plain data types shared between layers. No database or UI dependencies."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Movie:
    id: int
    title: str
    genre: str
    year: int
    rating: float
    votes: int
    poster_url: str | None


@dataclass(frozen=True)
class MovieFilters:
    genres: tuple[str, ...] = ()
    year_range: tuple[int, int] = (1900, 2100)
    min_rating: float = 0.0
    match_mood: bool = False
    mood: int = 3
    pace: int = 3


@dataclass(frozen=True)
class RatingStats:
    average: float | None
    count: int
