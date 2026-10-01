"""
Database layer: table definitions, one pooled engine per access mode, and a
session context manager. Nothing outside this module creates engines.
"""
import atexit
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config import admin_database_url, database_url

Base = declarative_base()


class MovieRow(Base):
    __tablename__ = "movies"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="movies_rating_range"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    rating = Column(Float)
    votes = Column(Integer, default=0)
    poster_url = Column(String)


class RatingRow(Base):
    __tablename__ = "ratings"
    __table_args__ = (CheckConstraint("rating >= 0.5 AND rating <= 5", name="ratings_rating_range"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
    rating = Column(Float, nullable=False)


_engines: dict[bool, Engine] = {}


def get_engine(read_only: bool = True) -> Engine:
    """
    One pooled engine per mode, created on first use.

    Read-only engines use DATABASE_URL and ask PostgreSQL to reject writes for
    every transaction, so the web app cannot modify data even if a bug tries to.
    Write engines (admin scripts only) use ADMIN_DATABASE_URL.
    """
    if read_only not in _engines:
        if read_only:
            _engines[True] = create_engine(
                database_url(),
                pool_pre_ping=True,
                connect_args={"options": "-c default_transaction_read_only=on"},
            )
        else:
            _engines[False] = create_engine(admin_database_url(), pool_pre_ping=True)
    return _engines[read_only]


@contextmanager
def session_scope(read_only: bool = True) -> Iterator[Session]:
    """Yield a session; commit on success (write mode), roll back on error, always close."""
    session = sessionmaker(bind=get_engine(read_only), expire_on_commit=False)()
    try:
        yield session
        if not read_only:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    Base.metadata.create_all(get_engine(read_only=False))


def drop_tables() -> None:
    Base.metadata.drop_all(get_engine(read_only=False))


@atexit.register
def dispose_engines() -> None:
    """Close pooled connections cleanly when the process exits."""
    while _engines:
        _, engine = _engines.popitem()
        engine.dispose()

