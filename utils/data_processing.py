from sqlalchemy import func
from models.database import Movie, Rating, get_session

def filter_movies(filters):
    session = get_session()
    query = session.query(Movie)

    # Filter by genres if any selected
    if filters["genres"]:
        query = query.filter(Movie.genre.in_(filters["genres"]))

    # Filter by year range and rating
    query = query.filter(
        Movie.year >= filters["year_range"][0],
        Movie.year <= filters["year_range"][1],
        Movie.rating >= filters["min_rating"]
    )

    # Apply mood and pace filters (placeholder - would need actual mood/pace data in database)
    # TODO: Implement mood and pace filtering when data is available

    movies = query.all()
    session.close()
    return movies

def search_movies(search_term):
    if not search_term:
        return []

    session = get_session()
    movies = session.query(Movie).filter(
        Movie.title.ilike(f"%{search_term}%")
    ).all()
    session.close()
    return movies

def get_movie_rating_stats(movie_id):
    session = get_session()
    stats = session.query(
        func.avg(Rating.rating).label('avg_rating'),
        func.count(Rating.id).label('num_ratings')
    ).filter(Rating.movie_id == movie_id).first()
    session.close()
    return stats