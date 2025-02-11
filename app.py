import streamlit as st
from models.database import init_db, Movie, get_session
from models.recommender import MovieRecommender
from components.sidebar import render_sidebar
from components.movie_tiles import display_movie_tiles, display_watchlist
from utils.data_processing import filter_movies, search_movies, get_movie_rating_stats

# Initialize database if not exists
init_db()

# Page config
st.set_page_config(
    page_title="AI Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# Initialize session state
if 'recommender' not in st.session_state:
    st.session_state.recommender = MovieRecommender()

# Get unique genres and create movies dictionary
session = get_session()
genres = [g[0] for g in session.query(Movie.genre).distinct()]
movies_dict = {movie.id: movie for movie in session.query(Movie).all()}
session.close()

# Main layout
st.title("🎬 AI Movie Recommender")

# Sidebar filters
filters = render_sidebar(genres)

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Movies", "AI Recommendations", "Watchlist"])

with tab1:
    # Search box
    search_term = st.text_input("🔍 Search for movies", "")

    if search_term:
        results = search_movies(search_term)
        if results:
            st.subheader("Search Results")
            display_movie_tiles(results, section_prefix="search")
        else:
            st.warning("No movies found matching your search.")
    else:
        # Display filtered movies
        filtered_movies = filter_movies(filters)
        if filtered_movies:
            display_movie_tiles(filtered_movies, section_prefix="browse")
        else:
            st.warning("No movies found matching your filters.")

with tab2:
    st.subheader("AI Recommended Movies")
    recommended_movies = []
    if filters["genres"]:
        for genre in filters["genres"]:
            genre_recommendations = st.session_state.recommender.get_recommendations_by_genre(genre, n=2)
            if genre_recommendations:
                recommended_movies.extend(genre_recommendations)
        if recommended_movies:
            display_movie_tiles(recommended_movies, section_prefix="recommended")
        else:
            st.info("No recommendations found for the selected genres.")
    else:
        st.info("Please select at least one genre to get personalized recommendations.")

with tab3:
    st.subheader("Your Watchlist")
    display_watchlist(movies_dict)  # This function already uses "watchlist" as section prefix

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Gerald")