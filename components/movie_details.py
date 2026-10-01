import streamlit as st

from components.safe import escape_markdown, safe_poster
from models.domain import Movie, RatingStats


def render_details(movie: Movie, stats: RatingStats, similar: list[Movie]) -> None:
    poster_col, info_col = st.columns([1, 2])
    poster_col.image(safe_poster(movie.poster_url), width="stretch")
    with info_col:
        st.markdown(f"### {escape_markdown(movie.title)} ({movie.year})")
        st.markdown(f"🎭 {escape_markdown(movie.genre)}")
        rating_col, votes_col = st.columns(2)
        rating_col.metric("Rating", f"{movie.rating:.1f} / 5")
        votes_col.metric("User ratings", f"{stats.count:,}")
        if similar:
            st.markdown("**People who liked this also liked**")
            for other in similar:
                st.markdown(f"- {escape_markdown(other.title)} ({other.year}) · ⭐ {other.rating:.1f}")
