import os

import pytest

import models.database as database
import services.posters as posters


@pytest.fixture
def pg(monkeypatch):
    """Point the app at TEST_DATABASE_URL (both connections) and stub network poster lookups."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL to run integration tests")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("ADMIN_DATABASE_URL", url)
    monkeypatch.setattr(posters, "poster_url_for", lambda title, year=None: posters.placeholder_poster(title))
    database.dispose_engines()
    database.drop_tables()
    database.create_tables()
    yield url
    database.drop_tables()
    database.dispose_engines()
