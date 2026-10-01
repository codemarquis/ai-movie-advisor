"""
Seed data: a catalogue of real films plus synthetic user ratings.

Titles, years and genres are real. Ratings are generated: each synthetic
user has two favourite genres and rates films in them higher, which gives
the collaborative-filtering recommender real patterns to learn from.
Generation is deterministic (fixed seed), so every install gets the same data.
"""
import numpy as np
import pandas as pd

# (title, year, genre, baseline quality on a 1–5 scale)
CATALOG: list[tuple[str, int, str, float]] = [
    ("The Shawshank Redemption", 1994, "Drama", 4.7),
    ("The Godfather", 1972, "Crime", 4.6),
    ("Pulp Fiction", 1994, "Crime", 4.4),
    ("The Dark Knight", 2008, "Action", 4.5),
    ("Forrest Gump", 1994, "Drama", 4.3),
    ("Inception", 2010, "Sci-Fi", 4.4),
    ("The Matrix", 1999, "Sci-Fi", 4.4),
    ("Goodfellas", 1990, "Crime", 4.4),
    ("The Silence of the Lambs", 1991, "Thriller", 4.3),
    ("Fight Club", 1999, "Drama", 4.3),
    ("Interstellar", 2014, "Sci-Fi", 4.3),
    ("Gladiator", 2000, "Action", 4.2),
    ("Spirited Away", 2001, "Animation", 4.5),
    ("Toy Story", 1995, "Animation", 4.2),
    ("The Lion King", 1994, "Animation", 4.2),
    ("Jurassic Park", 1993, "Adventure", 4.1),
    ("Back to the Future", 1985, "Adventure", 4.3),
    ("Alien", 1979, "Horror", 4.2),
    ("The Shining", 1980, "Horror", 4.2),
    ("Get Out", 2017, "Horror", 4.0),
    ("Parasite", 2019, "Thriller", 4.4),
    ("Memento", 2000, "Thriller", 4.2),
    ("The Grand Budapest Hotel", 2014, "Comedy", 4.1),
    ("Groundhog Day", 1993, "Comedy", 4.0),
    ("The Big Lebowski", 1998, "Comedy", 4.0),
    ("Superbad", 2007, "Comedy", 3.7),
    ("Titanic", 1997, "Romance", 3.9),
    ("La La Land", 2016, "Musical", 4.0),
    ("The Notebook", 2004, "Romance", 3.7),
    ("Amélie", 2001, "Romance", 4.1),
    ("Saving Private Ryan", 1998, "War", 4.3),
    ("Dunkirk", 2017, "War", 3.9),
    ("Hacksaw Ridge", 2016, "War", 4.0),
    ("Unforgiven", 1992, "Western", 4.1),
    ("Django Unchained", 2012, "Western", 4.2),
    ("The Revenant", 2015, "Western", 3.9),
    ("Mad Max: Fury Road", 2015, "Action", 4.1),
    ("The Lord of the Rings: The Fellowship of the Ring", 2001, "Fantasy", 4.5),
    ("Harry Potter and the Philosopher's Stone", 2001, "Fantasy", 3.9),
    ("Pan's Labyrinth", 2006, "Fantasy", 4.1),
    ("Finding Nemo", 2003, "Family", 4.0),
    ("Paddington 2", 2017, "Family", 4.1),
    ("Coco", 2017, "Animation", 4.2),
    ("Free Solo", 2018, "Documentary", 4.0),
    ("March of the Penguins", 2005, "Documentary", 3.8),
    ("Knives Out", 2019, "Mystery", 4.0),
    ("Gone Girl", 2014, "Mystery", 4.0),
    ("Chinatown", 1974, "Film-Noir", 4.2),
    ("L.A. Confidential", 1997, "Film-Noir", 4.1),
    ("Whiplash", 2014, "Drama", 4.4),
]


def build_catalog() -> pd.DataFrame:
    """Catalogue with stable ids 1..N: columns movie_id, title, year, genre, quality."""
    df = pd.DataFrame(CATALOG, columns=["title", "year", "genre", "quality"])
    df.insert(0, "movie_id", range(1, len(df) + 1))
    return df


def generate_ratings(catalog: pd.DataFrame, num_users: int = 300, seed: int = 42) -> pd.DataFrame:
    """Synthetic ratings (user_id, movie_id, rating), one per user/movie pair, in 0.5 steps."""
    rng = np.random.default_rng(seed)
    genres = sorted(catalog["genre"].unique())
    rows = []
    for user_id in range(1, num_users + 1):
        favourites = set(rng.choice(genres, size=2, replace=False))
        in_taste = catalog["genre"].isin(favourites).to_numpy()
        # Users mostly watch what they like, plus some random picks.
        weights = np.where(in_taste, 4.0, 1.0)
        count = int(rng.integers(12, 31))
        picks = rng.choice(len(catalog), size=count, replace=False, p=weights / weights.sum())
        user_bias = rng.normal(0, 0.3)
        for i in picks:
            movie = catalog.iloc[i]
            taste = 0.6 if in_taste[i] else -0.5
            score = movie["quality"] + taste + user_bias + rng.normal(0, 0.45)
            rows.append(
                {"user_id": user_id, "movie_id": int(movie["movie_id"]),
                 "rating": float(np.clip(np.round(score * 2) / 2, 0.5, 5.0))}
            )
    return pd.DataFrame(rows, columns=["user_id", "movie_id", "rating"])
