"""
Resolve a real poster image URL for a movie title.

Order of sources:
  1. TMDB, when TMDB_API_KEY is set (the canonical movie-poster source)
  2. Wikipedia's page-summary API (no key needed; the lead image of a film
     article is its theatrical poster)
  3. A placeholder card showing the title, so a tile is never blank
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Optional

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia asks API clients to identify themselves
USER_AGENT = "ai-movie-advisor/1.0 (https://github.com/codemarquis/ai-movie-advisor)"

try:
    # Some Python builds (e.g. python.org on macOS) ship without root certificates;
    # certifi's bundle comes with streamlit's dependencies.
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()


def _warn(message: str) -> None:
    print(f"[posters] {message}", file=sys.stderr)


def placeholder_poster(title: str) -> str:
    return f"https://placehold.co/300x450/1f2937/e5e7eb?text={urllib.parse.quote_plus(title)}"


def _tmdb_poster(title: str) -> Optional[str]:
    if not os.getenv("TMDB_API_KEY"):
        return None
    try:
        from tmdbv3api import TMDb, Movie
        tmdb = TMDb()
        tmdb.api_key = os.getenv("TMDB_API_KEY")
        for result in Movie().search(title):
            if getattr(result, "poster_path", None):
                return f"{TMDB_IMAGE_BASE}{result.poster_path}"
    except Exception as exc:
        _warn(f"TMDB lookup failed for {title!r}: {exc}")
    return None


def _wikipedia_poster(title: str) -> Optional[str]:
    # Try the "(film)" disambiguation first: the bare title is sometimes the
    # source novel (e.g. "The Silence of the Lambs").
    for page in (f"{title} (film)", title):
        url = WIKI_SUMMARY + urllib.parse.quote(page.replace(" ", "_"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:  # 404 just means no such page; try the next candidate
                _warn(f"Wikipedia lookup failed for {page!r}: {exc}")
            continue
        except Exception as exc:
            _warn(f"Wikipedia lookup failed for {page!r}: {exc}")
            continue
        if data.get("type") != "standard" or "film" not in (data.get("description") or "").lower():
            continue
        image = data.get("originalimage") or data.get("thumbnail") or {}
        if image.get("source"):
            return image["source"]
    return None


@lru_cache(maxsize=None)
def poster_url_for(title: str) -> str:
    """Best available poster URL for a title; cached per process."""
    return _tmdb_poster(title) or _wikipedia_poster(title) or placeholder_poster(title)
