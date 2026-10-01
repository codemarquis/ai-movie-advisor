"""Run against a real PostgreSQL: TEST_DATABASE_URL=postgresql://… pytest -m integration"""
import json

import export_db
import import_db
import init_db
import pytest
from sqlalchemy import text

import models.database as database
from models.domain import MovieFilters
from repositories import movie_repository as repo
from services.mood import genres_matching

pytestmark = pytest.mark.integration


def test_seed_is_idempotent(pg, capsys):
    assert init_db.main([]) == 0
    assert repo.movie_count() == 50
    assert init_db.main([]) == 0
    assert "nothing to do" in capsys.readouterr().out
    assert repo.movie_count() == 50


def test_search_treats_wildcards_literally(pg):
    init_db.main([])
    assert repo.search_movies("%") == []
    assert repo.search_movies("_") == []
    assert [m.title for m in repo.search_movies("  matrix ")] == ["The Matrix"]
    assert repo.search_movies("x" * 10_000) == []  # capped, no error


def test_mood_filter_only_returns_matching_genres(pg):
    init_db.main([])
    movies = repo.find_movies(MovieFilters(match_mood=True, mood=5, pace=4))
    assert movies
    assert {m.genre for m in movies} <= genres_matching(5, 4)


def test_app_connection_cannot_write(pg):
    init_db.main([])
    with pytest.raises(Exception, match="read-only"):
        with database.get_engine(read_only=True).begin() as conn:
            conn.execute(text("DELETE FROM ratings"))


def test_export_import_round_trip(pg, tmp_path):
    init_db.main([])
    export_db.export(tmp_path)
    assert "CREATE TABLE movies" in (tmp_path / "schema.sql").read_text()
    database.drop_tables()
    rows = import_db.import_data(tmp_path / "data.json")
    assert rows == 50 + len(json.loads((tmp_path / "data.json").read_text())["ratings"])
    assert repo.movie_count() == 50


@pytest.mark.parametrize("payload", [
    {"pg_authid": []},
    {"movies": [{"id": 1, "title": "t", "genre": "Drama", "year": 2000, "evil": 1}]},
    ["not", "an", "object"],
])
def test_import_rejects_unknown_tables_and_columns(pg, tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(import_db.ImportRejected):
        import_db.import_data(path)
