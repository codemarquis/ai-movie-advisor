import pandas as pd
import numpy as np

def generate_mock_data():
    # Generate mock movie data
    movies_data = {
        'movie_id': range(1, 101),
        'title': [
            'The Shawshank Redemption', 'The Godfather', 'Pulp Fiction', 
            'The Dark Knight', 'Forrest Gump', 'Inception', 'The Matrix',
            'Goodfellas', 'The Silence of the Lambs', 'Fight Club'
        ] * 10,  # Repeating movies to create more data
        'genre': [
            'Drama', 'Crime', 'Crime', 'Action', 'Drama', 'Sci-Fi',
            'Sci-Fi', 'Crime', 'Thriller', 'Drama'
        ] * 10,
        'year': np.random.randint(1990, 2023, 100),
        'rating': np.random.uniform(3.0, 5.0, 100).round(1),
        'votes': np.random.randint(1000, 100000, 100)
    }

    # Generate mock user ratings with unique user-movie combinations
    num_users = 1000
    num_movies = 100
    num_ratings = 5000

    # Generate unique user-movie pairs
    user_ids = np.random.randint(1, num_users + 1, num_ratings)
    movie_ids = np.random.randint(1, num_movies + 1, num_ratings)

    # Create DataFrame and drop duplicates to ensure uniqueness
    user_ratings = pd.DataFrame({
        'user_id': user_ids,
        'movie_id': movie_ids,
        'rating': np.random.uniform(1.0, 5.0, num_ratings).round(1)
    }).drop_duplicates(subset=['user_id', 'movie_id'])

    movies_df = pd.DataFrame(movies_data)
    movies_df = add_poster_urls(movies_df)
    return movies_df, user_ratings

def add_poster_urls(movies_df):
    """Add reliable placeholder images for movie posters"""
    # Movie posters with different designs for each genre
    genre_colors = {
        'Drama': '2c3e50',
        'Crime': '8e44ad',
        'Action': 'e74c3c',
        'Sci-Fi': '3498db',
        'Thriller': '27ae60'
    }

    for idx, row in movies_df.iterrows():
        genre = row['genre']
        color = genre_colors.get(genre, '34495e')  # Default color if genre not in mapping

        # Create a movie-themed placeholder with title and year
        text = f"{row['title'].replace(' ', '+')}+({row['year']})"
        bg_color = color
        text_color = 'ffffff'

        # Using a reliable placeholder service
        movies_df.at[idx, 'poster_url'] = (
            f"https://placehold.co/300x450/{bg_color}/{text_color}?"
            f"text={text}"
        )

    return movies_df