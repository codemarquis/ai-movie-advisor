from tmdbv3api import TMDb, Movie, Discover
import os
from typing import List, Dict, Optional
import streamlit as st

class TMDBService:
    def __init__(self):
        self.tmdb = TMDb()
        self.tmdb.api_key = os.getenv('TMDB_API_KEY')
        self.movie = Movie()
        self.discover = Discover()
        self.base_image_url = "https://image.tmdb.org/t/p/w500"

    @st.cache_data(ttl=3600)
    def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """Fetch popular movies with caching"""
        try:
            movies = self.movie.popular(page=page)
            return [self._format_movie_data(movie) for movie in movies]
        except Exception as e:
            st.error(f"Error fetching popular movies: {str(e)}")
            return []

    @st.cache_data(ttl=3600)
    def search_movies(self, query: str) -> List[Dict]:
        """Search movies by title with caching"""
        try:
            movies = self.movie.search(query)
            return [self._format_movie_data(movie) for movie in movies]
        except Exception as e:
            st.error(f"Error searching movies: {str(e)}")
            return []

    @st.cache_data(ttl=3600)
    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> List[Dict]:
        """Get movies by genre with caching"""
        try:
            movies = self.discover.discover_movies({
                'with_genres': genre_id,
                'page': page
            })
            return [self._format_movie_data(movie) for movie in movies]
        except Exception as e:
            st.error(f"Error fetching movies by genre: {str(e)}")
            return []

    def _format_movie_data(self, movie) -> Dict:
        """Format TMDB movie data into our application format"""
        return {
            'id': movie.id,
            'title': movie.title,
            'genre_ids': getattr(movie, 'genre_ids', []),
            'year': movie.release_date[:4] if hasattr(movie, 'release_date') and movie.release_date else None,
            'rating': getattr(movie, 'vote_average', 0.0),
            'votes': getattr(movie, 'vote_count', 0),
            'poster_url': f"{self.base_image_url}{movie.poster_path}" if movie.poster_path else f"https://placehold.co/300x450/darkgray/white?text={movie.title.replace(' ', '+')}",
            'overview': getattr(movie, 'overview', ''),
            'popularity': getattr(movie, 'popularity', 0.0)
        }

    @st.cache_data(ttl=3600)
    def get_genre_list(self) -> List[Dict]:
        """Get list of movie genres"""
        try:
            genres = self.movie.genres()
            return [{'id': genre.id, 'name': genre.name} for genre in genres]
        except Exception as e:
            st.error(f"Error fetching genres: {str(e)}")
            return []
