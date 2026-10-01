"""
Item-based collaborative filtering.

Pure computation: takes a ratings DataFrame (user_id, movie_id, rating) and
returns movie ids. It knows nothing about the database or the UI.
"""
from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class MovieRecommender:
    def __init__(self, ratings: pd.DataFrame):
        self._movie_ids: list[int] = []
        self._index: dict[int, int] = {}
        self._similarity: np.ndarray | None = None
        if ratings.empty:
            return
        # Rows = users, columns = movies. Similarity rows/columns follow the
        # column order, so ids are mapped from the matrix columns, not from a
        # separate movie list (the bug this replaces).
        matrix = ratings.pivot_table(index="user_id", columns="movie_id", values="rating", aggfunc="mean")
        matrix = matrix.fillna(0.0)
        self._movie_ids = [int(m) for m in matrix.columns]
        self._index = {movie_id: i for i, movie_id in enumerate(self._movie_ids)}
        self._similarity = cosine_similarity(matrix.T.to_numpy())

    def similar_to(self, movie_id: int, n: int = 5) -> list[int]:
        """Movies whose rating patterns are most similar to `movie_id`."""
        return self.recommend_for([movie_id], n)

    def recommend_for(self, movie_ids: Iterable[int], n: int = 8) -> list[int]:
        """Movies most similar to the given set, excluding the set itself."""
        if self._similarity is None:
            return []
        seeds = {int(m) for m in movie_ids}
        rows = [self._index[m] for m in seeds if m in self._index]
        if not rows:
            return []
        scores = self._similarity[rows].sum(axis=0)
        ranked = np.argsort(-scores, kind="stable")
        result = [self._movie_ids[i] for i in ranked if self._movie_ids[i] not in seeds and scores[i] > 0]
        return result[:n]
