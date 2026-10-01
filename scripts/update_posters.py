"""
Re-resolve poster URLs for every movie already in the database.

Use this on an existing database instead of reseeding:
    python scripts/update_posters.py
"""
import _bootstrap  # noqa: F401

from repositories import movie_repository as repo
from services.posters import poster_url_for

if __name__ == "__main__":
    print(f"Updated posters for {repo.update_poster_urls(poster_url_for)} movies.")
