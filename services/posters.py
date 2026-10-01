"""
Resolve a real poster image URL for a movie.

Order of sources:
  1. TMDB, when TMDB_API_KEY is set (the canonical movie-poster source)
  2. Wikipedia's page-summary API (no key needed; the lead image of a film
     article is its theatrical poster)
  3. A placeholder card showing the title, so a tile is never blank

Responses from both sources are treated as untrusted: only https image URLs
are accepted, and the API key is scrubbed from anything that gets logged.
"""
import json
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request
from functools import cache

from config import tmdb_api_key

log = logging.getLogger(__name__)

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia asks API clients to identify themselves.
USER_AGENT = "ai-movie-advisor/1.0 (https://github.com/codemarquis/ai-movie-advisor)"
TIMEOUT_SECONDS = 10

try:
    # Some Python builds (e.g. python.org on macOS) ship without root certificates.
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # pragma: no cover
    _SSL_CONTEXT = ssl.create_default_context()


def placeholder_poster(title: str) -> str:
    return f"https://placehold.co/300x450/1f2937/e5e7eb?text={urllib.parse.quote_plus(title)}"


def _https_only(url: object) -> str | None:
    return url if isinstance(url, str) and url.startswith("https://") else None


def _redact(message: str) -> str:
    key = tmdb_api_key()
    return message.replace(key, "***") if key else message


def _tmdb_poster(title: str, year: int | None) -> str | None:
    key = tmdb_api_key()
    if not key:
        return None
    try:
        from tmdbv3api import Movie, TMDb

        TMDb().api_key = key
        for result in Movie().search(title):
            release = str(getattr(result, "release_date", "") or "")
            if year and release and not release.startswith(str(year)):
                continue
            path = getattr(result, "poster_path", None)
            if isinstance(path, str) and path.startswith("/"):
                return f"{TMDB_IMAGE_BASE}{urllib.parse.quote(path)}"
    except Exception as exc:
        log.warning("TMDB lookup failed for %r: %s", title, _redact(str(exc)))
    return None


def _wiki_summary(page: str) -> dict | None:
    url = WIKI_SUMMARY + urllib.parse.quote(page.replace(" ", "_"), safe="")
    # Fixed https host built above, so no file:// or custom schemes can reach urlopen.
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS, context=_SSL_CONTEXT) as resp:  # noqa: S310
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:  # 404 only means "no such page"
            log.warning("Wikipedia lookup failed for %r: %s", page, exc)
        return None
    except Exception as exc:
        log.warning("Wikipedia lookup failed for %r: %s", page, exc)
        return None
    return data if isinstance(data, dict) else None


def _wikipedia_poster(title: str, year: int | None) -> str | None:
    # Most specific page first: "Titanic (1997 film)", then "Titanic (film)",
    # then "Titanic". The bare title can be a novel or a ship.
    pages = ([f"{title} ({year} film)"] if year else []) + [f"{title} (film)", title]
    for page in pages:
        data = _wiki_summary(page)
        if not data or data.get("type") != "standard":
            continue
        if "film" not in str(data.get("description") or "").lower():
            continue
        image = data.get("originalimage") or data.get("thumbnail") or {}
        url = _https_only(image.get("source") if isinstance(image, dict) else None)
        if url:
            return url
    return None


@cache
def poster_url_for(title: str, year: int | None = None) -> str:
    """Best available poster URL for a film; cached per process."""
    return _tmdb_poster(title, year) or _wikipedia_poster(title, year) or placeholder_poster(title)
