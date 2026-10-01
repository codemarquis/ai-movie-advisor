import pytest

import config


def test_missing_database_url_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(config.ConfigError, match="DATABASE_URL is not set"):
        config.database_url()


def test_non_postgres_url_is_rejected(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    with pytest.raises(config.ConfigError, match="PostgreSQL"):
        config.database_url()


def test_driver_is_pinned_to_psycopg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    assert config.database_url() == "postgresql+psycopg://u:p@h/db"


def test_admin_url_falls_back_to_app_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://app@h/db")
    monkeypatch.delenv("ADMIN_DATABASE_URL", raising=False)
    assert config.admin_database_url() == "postgresql+psycopg://app@h/db"
    monkeypatch.setenv("ADMIN_DATABASE_URL", "postgresql://admin@h/db")
    assert config.admin_database_url() == "postgresql+psycopg://admin@h/db"


def test_blank_tmdb_key_is_none(monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", "  ")
    assert config.tmdb_api_key() is None
