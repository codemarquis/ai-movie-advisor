import streamlit as st

from models.domain import MovieFilters


def render_sidebar(genres: list[str], year_bounds: tuple[int, int]) -> MovieFilters:
    st.sidebar.title("Movie Filters")

    st.sidebar.subheader("Genres")
    select_all = st.sidebar.checkbox("Select all genres", key="genre_all")
    selected: list[str] = []
    if select_all:
        selected = list(genres)
    else:
        left, right = st.sidebar.columns(2)
        half = (len(genres) + 1) // 2
        for column, chunk in ((left, genres[:half]), (right, genres[half:])):
            with column:
                selected += [g for g in chunk if st.checkbox(g, key=f"genre_{g}")]

    st.sidebar.subheader("Mood & pace")
    match_mood = st.sidebar.toggle(
        "Match my mood & pace",
        key="match_mood",
        help="Keeps genres whose typical mood and pace are close to your choice.",
    )
    mood = st.sidebar.slider(
        "Mood", 1, 5, 3, disabled=not match_mood, help="1: Light & fun → 5: Dark & serious"
    )
    pace = st.sidebar.slider(
        "Pace", 1, 5, 3, disabled=not match_mood, help="1: Slow & thoughtful → 5: Fast & action-packed"
    )

    low, high = year_bounds
    if low >= high:
        high = low + 1
    year_range = st.sidebar.slider("Year range", low, high, (low, high))
    min_rating = st.sidebar.slider("Minimum rating", 0.0, 5.0, 0.0, 0.5)

    return MovieFilters(
        genres=tuple(selected),
        year_range=year_range,
        min_rating=min_rating,
        match_mood=match_mood,
        mood=mood,
        pace=pace,
    )
