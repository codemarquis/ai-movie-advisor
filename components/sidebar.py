import streamlit as st

def render_sidebar(genres):
    st.sidebar.title("Movie Filters")

    # Extended genre list
    all_genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime", 
        "Documentary", "Drama", "Family", "Fantasy", "Film-Noir",
        "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
        "Thriller", "War", "Western"
    ]

    # Genre checkboxes
    st.sidebar.subheader("Genres")
    select_all = st.sidebar.checkbox("Select All Genres")

    selected_genres = []
    if select_all:
        selected_genres = all_genres
    else:
        # Create two columns for genres
        col1, col2 = st.sidebar.columns(2)

        # Split genres between columns
        half = len(all_genres) // 2
        with col1:
            for genre in all_genres[:half]:
                if st.checkbox(genre, key=f"genre_{genre}"):
                    selected_genres.append(genre)

        with col2:
            for genre in all_genres[half:]:
                if st.checkbox(genre, key=f"genre_{genre}"):
                    selected_genres.append(genre)

    # Mood slider
    mood = st.sidebar.slider(
        "Mood",
        min_value=1,
        max_value=5,
        value=3,
        help="1: Light & Fun → 5: Dark & Serious"
    )

    # Pace slider
    pace = st.sidebar.slider(
        "Pace",
        min_value=1,
        max_value=5,
        value=3,
        help="1: Slow & Thoughtful → 5: Fast & Action-packed"
    )

    # Year range filter
    year_range = st.sidebar.slider(
        "Select Year Range",
        1990, 2023, (1990, 2023)
    )

    # Rating filter
    min_rating = st.sidebar.slider(
        "Minimum Rating",
        1.0, 5.0, 3.0, 0.5
    )

    return {
        "genres": selected_genres,
        "mood": mood,
        "pace": pace,
        "year_range": year_range,
        "min_rating": min_rating
    }