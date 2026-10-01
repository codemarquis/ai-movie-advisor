"""
Refresh poster URLs for every movie already in the database.

Use this on an existing database instead of re-seeding:
    python scripts/update_posters.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Movie, get_session
from services.posters import poster_url_for


def update_posters():
    session = get_session()
    movies = session.query(Movie).all()
    for movie in movies:
        movie.poster_url = poster_url_for(movie.title)
    session.commit()
    session.close()
    print(f"Updated posters for {len(movies)} movies")


if __name__ == "__main__":
    update_posters()
