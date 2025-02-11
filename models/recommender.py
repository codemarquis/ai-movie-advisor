import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from models.database import Movie, Rating, get_session
import pandas as pd

class MovieRecommender:
    def __init__(self):
        self.similarity_matrix = None
        self.movies_map = {}
        self._prepare_data()

    def _prepare_data(self):
        session = get_session()

        # Get all ratings
        ratings = session.query(Rating).all()

        # Create user-movie matrix using pandas
        ratings_data = {
            'user_id': [r.user_id for r in ratings],
            'movie_id': [r.movie_id for r in ratings],
            'rating': [r.rating for r in ratings]
        }
        ratings_df = pd.DataFrame(ratings_data)

        # Create user-movie matrix
        self.user_movie_matrix = ratings_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            aggfunc='mean'
        ).fillna(0)

        # Calculate movie similarity matrix
        movie_matrix = self.user_movie_matrix.T
        self.similarity_matrix = cosine_similarity(movie_matrix)

        # Create movie id to index mapping
        movies = session.query(Movie).all()
        self.movies_map = {m.id: idx for idx, m in enumerate(movies)}

        session.close()

    def get_similar_movies(self, movie_id, n=5):
        session = get_session()
        try:
            movie_idx = self.movies_map[movie_id]
            sim_scores = list(enumerate(self.similarity_matrix[movie_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:n+1]
            movie_indices = [i[0] for i in sim_scores]

            # Get movie objects from database
            similar_movies = session.query(Movie).filter(
                Movie.id.in_([list(self.movies_map.keys())[i] for i in movie_indices])
            ).all()

            session.close()
            return similar_movies
        except (KeyError, IndexError):
            session.close()
            return None

    def get_recommendations_by_genre(self, genre, n=5):
        session = get_session()
        movies = session.query(Movie).filter(
            Movie.genre == genre
        ).order_by(Movie.rating.desc()).limit(n).all()
        session.close()
        return movies