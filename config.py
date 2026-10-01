"""
Application configuration.

Settings come from environment variables; a local `.env` file is loaded if
present (real environment variables win). Nothing is hard-coded, and secret
values are never logged or shown in the UI.
"""
import os

from dotenv import load_dotenv

load_dotenv(override=False)

_SCHEMES = ("postgresql://", "postgresql+psycopg://")


class ConfigError(RuntimeError):
    """Required configuration is missing or invalid."""


def _postgres_url(name: str, value: str) -> str:
    value = value.strip()
    if not value.startswith(_SCHEMES):
        raise ConfigError(f"{name} must be a PostgreSQL URL starting with postgresql://")
    # Pin the psycopg (v3) driver so behaviour doesn't depend on the SQLAlchemy version's default.
    return value.replace("postgresql://", "postgresql+psycopg://", 1)


def database_url() -> str:
    """Connection used by the web app. Should be a read-only database role."""
    value = os.getenv("DATABASE_URL", "")
    if not value.strip():
        raise ConfigError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return _postgres_url("DATABASE_URL", value)


def admin_database_url() -> str:
    """Connection used by admin scripts that write (seed, import, poster refresh)."""
    value = os.getenv("ADMIN_DATABASE_URL", "")
    return _postgres_url("ADMIN_DATABASE_URL", value) if value.strip() else database_url()


def tmdb_api_key() -> str | None:
    return os.getenv("TMDB_API_KEY", "").strip() or None
