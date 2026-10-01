import pandas as pd

from services.recommender import MovieRecommender


def ratings(rows):
    return pd.DataFrame(rows, columns=["user_id", "movie_id", "rating"])


def test_similarity_maps_back_to_the_right_movie_ids():
    # Non-contiguous ids and a movie (99) nobody rated: the old implementation
    # indexed similarities by catalogue position and returned the wrong films.
    df = ratings([
        (1, 10, 5), (1, 20, 5), (1, 30, 1),
        (2, 10, 4), (2, 20, 5), (2, 30, 1),
        (3, 30, 5), (3, 40, 5), (3, 10, 1),
        (4, 30, 4), (4, 40, 5),
    ])
    rec = MovieRecommender(df)
    assert rec.similar_to(10, n=1) == [20]
    assert rec.similar_to(40, n=1) == [30]
    assert rec.similar_to(99) == []


def test_recommend_for_excludes_seeds_and_ranks_by_similarity():
    df = ratings([(u, m, 5) for u in (1, 2, 3) for m in (1, 2, 3)] + [(4, 4, 5), (4, 1, 1)])
    rec = MovieRecommender(df)
    picks = rec.recommend_for({1, 2})
    assert 1 not in picks and 2 not in picks
    assert picks[0] == 3


def test_empty_ratings_recommend_nothing():
    rec = MovieRecommender(ratings([]))
    assert rec.similar_to(1) == [] and rec.recommend_for([1]) == []
