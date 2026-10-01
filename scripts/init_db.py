"""
Create the tables and seed the catalogue.

Safe to run more than once: if movies already exist it does nothing.
Pass --reset to drop and recreate every table first (destroys all data).
Uses ADMIN_DATABASE_URL (falls back to DATABASE_URL).
"""
import argparse

import _bootstrap  # noqa: F401

from data.seed import build_catalog, generate_ratings
from models.database import create_tables, drop_tables
from repositories import movie_repository as repo
from services.posters import poster_url_for


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first (destroys data)")
    args = parser.parse_args(argv)

    if args.reset:
        drop_tables()
    create_tables()

    existing = repo.movie_count()
    if existing:
        print(f"Database already has {existing} movies; nothing to do. Use --reset to reseed.")
        return 0

    catalog = build_catalog()
    ratings = generate_ratings(catalog)
    stats = ratings.groupby("movie_id")["rating"].agg(["mean", "count"])

    movies = []
    for m in catalog.itertuples():
        mean, count = (stats.loc[m.movie_id] if m.movie_id in stats.index else (None, 0))
        movies.append({
            "id": int(m.movie_id),
            "title": m.title,
            "genre": m.genre,
            "year": int(m.year),
            "rating": round(float(mean), 1) if mean is not None else None,
            "votes": int(count),
            "poster_url": poster_url_for(m.title, int(m.year)),
        })
    repo.insert_catalog(movies, ratings.to_dict("records"))
    print(f"Seeded {len(movies)} movies and {len(ratings)} ratings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
