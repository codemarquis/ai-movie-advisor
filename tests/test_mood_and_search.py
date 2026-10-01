from repositories.movie_repository import escape_like
from services.mood import GENRE_PROFILES, genres_matching


def test_genres_matching_respects_tolerance():
    assert genres_matching(5, 4) == {"Horror", "Thriller", "War", "Crime"} & {
        g for g, (m, p) in GENRE_PROFILES.items() if abs(m - 5) <= 1 and abs(p - 4) <= 1
    }
    assert "Comedy" not in genres_matching(5, 4)
    assert genres_matching(1, 3, tolerance=0) == {"Animation", "Comedy", "Musical"}


def test_escape_like_makes_wildcards_literal():
    assert escape_like("100%_off\\") == "100\\%\\_off\\\\"
    assert escape_like("matrix") == "matrix"
