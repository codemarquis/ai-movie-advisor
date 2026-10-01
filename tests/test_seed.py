from data.seed import build_catalog, generate_ratings
from services.mood import GENRE_PROFILES


def test_catalog_has_unique_real_titles_and_known_genres():
    catalog = build_catalog()
    assert catalog["title"].is_unique
    assert catalog["movie_id"].tolist() == list(range(1, len(catalog) + 1))
    assert set(catalog["genre"]) <= set(GENRE_PROFILES)
    assert catalog["year"].between(1900, 2030).all()


def test_ratings_are_valid_unique_and_deterministic():
    catalog = build_catalog()
    first, second = generate_ratings(catalog), generate_ratings(catalog)
    assert first.equals(second)
    assert not first.duplicated(["user_id", "movie_id"]).any()
    assert first["rating"].between(0.5, 5.0).all()
    assert ((first["rating"] * 2) % 1 == 0).all()  # half-star steps
    assert set(first["movie_id"]) <= set(catalog["movie_id"])
