import logging
import sys
import types

import pytest

import services.posters as posters


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    posters.poster_url_for.cache_clear()
    yield
    posters.poster_url_for.cache_clear()


def fake_wiki(pages):
    calls = []

    def summary(page):
        calls.append(page)
        return pages.get(page)

    return summary, calls


def film(url, description="1997 film by James Cameron"):
    return {"type": "standard", "description": description, "originalimage": {"source": url}}


def test_year_qualified_page_is_tried_first(monkeypatch):
    summary, calls = fake_wiki({"Titanic (1997 film)": film("https://upload.wikimedia.org/t.jpg")})
    monkeypatch.setattr(posters, "_wiki_summary", summary)
    assert posters.poster_url_for("Titanic", 1997) == "https://upload.wikimedia.org/t.jpg"
    assert calls == ["Titanic (1997 film)"]


def test_non_film_pages_are_skipped(monkeypatch):
    summary, _ = fake_wiki({
        "Titanic (film)": None,
        "Titanic": film("https://upload.wikimedia.org/ship.jpg", description="British ocean liner"),
    })
    monkeypatch.setattr(posters, "_wiki_summary", summary)
    assert posters.poster_url_for("Titanic").startswith("https://placehold.co/")


def test_non_https_image_urls_are_rejected(monkeypatch):
    summary, _ = fake_wiki({"X (film)": film("http://insecure.example/x.jpg")})
    monkeypatch.setattr(posters, "_wiki_summary", summary)
    assert posters.poster_url_for("X").startswith("https://placehold.co/")


def test_tmdb_errors_never_log_the_api_key(monkeypatch, caplog):
    secret = "sk-test-123456"
    monkeypatch.setenv("TMDB_API_KEY", secret)

    class ExplodingMovie:
        def search(self, title):
            raise RuntimeError(f"GET https://api.themoviedb.org/3/search?api_key={secret} failed")

    fake_tmdb = types.SimpleNamespace(TMDb=lambda: types.SimpleNamespace(), Movie=ExplodingMovie)
    monkeypatch.setitem(sys.modules, "tmdbv3api", fake_tmdb)
    monkeypatch.setattr(posters, "_wiki_summary", lambda page: None)
    with caplog.at_level(logging.WARNING):
        assert posters.poster_url_for("Anything").startswith("https://placehold.co/")
    assert secret not in caplog.text and "***" in caplog.text
