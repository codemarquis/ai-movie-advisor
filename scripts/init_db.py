import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, Movie, Rating, get_session
from data.mock_movies import generate_mock_data
from services.posters import poster_url_for

def populate_database():
    # Initialize database
    init_db()
    session = get_session()

    # Generate mock data
    movies_df, ratings_df = generate_mock_data()

    # Add movies
    for _, row in movies_df.iterrows():
        movie = Movie(
            id=int(row['movie_id']),
            title=str(row['title']),
            genre=str(row['genre']),
            year=int(row['year']),
            rating=float(row['rating']),
            votes=int(row['votes']),
            poster_url=poster_url_for(str(row['title']))
        )
        session.add(movie)

    # Commit movies first to establish foreign keys
    session.commit()

    # Add ratings
    for _, row in ratings_df.iterrows():
        rating = Rating(
            user_id=int(row['user_id']),
            movie_id=int(row['movie_id']),
            rating=float(row['rating'])
        )
        session.add(rating)

    session.commit()
    session.close()

if __name__ == "__main__":
    populate_database()