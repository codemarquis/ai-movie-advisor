"""
AI Movie Advisor: Streamlit entry point.

A thin controller: it asks the repository and services for data and hands
the results to UI components. No SQL lives here.
"""
import logging

import streamlit as st

from components.movie_details import render_details
from components.movie_tiles import TILE_CSS, display_movie_tiles
from components.sidebar import render_sidebar
from config import ConfigError
from repositories import movie_repository as repo
from services.recommender import MovieRecommender

log = logging.getLogger("ai_movie_advisor")

st.set_page_config(page_title="AI Movie Advisor", page_icon="🎬", layout="wide")


@st.cache_resource(ttl=3600)
def get_recommender() -> MovieRecommender:
    return MovieRecommender(repo.ratings_frame())


@st.cache_data(ttl=300)
def load_genres() -> list[str]:
    return repo.list_genres()


@st.cache_data(ttl=300)
def load_year_bounds() -> tuple[int, int]:
    return repo.year_bounds()


@st.dialog("Movie details", width="large")
def show_details(movie_id: int) -> None:
    movies = repo.get_movies([movie_id])
    if not movies:
        st.warning("This movie is no longer available.")
        return
    similar = repo.get_movies(get_recommender().similar_to(movie_id, n=5))
    render_details(movies[0], repo.rating_stats(movie_id), similar)


def tiles_or_message(movies, section: str, watchlist: set[int], empty_message: str) -> None:
    if movies:
        display_movie_tiles(movies, section, watchlist)
    else:
        st.info(empty_message)


def main() -> None:
    try:
        genres, year_bounds = load_genres(), load_year_bounds()
    except ConfigError as exc:
        st.error(str(exc))
        st.stop()
    except Exception:
        # Full details go to the server log; users get a generic message.
        log.exception("Database unavailable")
        st.error("The movie database is unavailable right now. Please try again shortly.")
        st.stop()

    watchlist: set[int] = st.session_state.setdefault("watchlist", set())
    st.markdown(TILE_CSS, unsafe_allow_html=True)  # static, trusted CSS only
    st.title("🎬 AI Movie Advisor")

    filters = render_sidebar(genres, year_bounds)
    browse_tab, recommend_tab, watchlist_tab = st.tabs(["Movies", "AI Recommendations", "Watchlist"])

    with browse_tab:
        term = st.text_input("🔍 Search by title", max_chars=repo.MAX_SEARCH_LENGTH).strip()
        if term:
            st.subheader("Search results")
            tiles_or_message(repo.search_movies(term), "search", watchlist, "No movies match that title.")
        else:
            tiles_or_message(repo.find_movies(filters), "browse", watchlist, "No movies match these filters.")

    with recommend_tab:
        if watchlist:
            st.subheader("Because of your watchlist")
            picks = repo.get_movies(get_recommender().recommend_for(watchlist, n=8))
            tiles_or_message(picks, "rec_watch", watchlist, "No similar movies found yet.")
        if filters.genres:
            st.subheader("Top picks in your genres")
            picks = [m for g in filters.genres for m in repo.top_rated_in_genre(g, limit=2)]
            tiles_or_message(picks, "rec_genre", watchlist, "No movies in these genres yet.")
        if not watchlist and not filters.genres:
            st.info("Add movies to your watchlist, or pick genres in the sidebar, to get recommendations.")

    with watchlist_tab:
        st.subheader("Your Watchlist")
        tiles_or_message(
            repo.get_movies(sorted(watchlist)), "watchlist", watchlist,
            "Your watchlist is empty. Use ➕ Watchlist on any movie to save it here.",
        )

    details_id = st.session_state.pop("details_id", None)
    if details_id is not None:
        show_details(details_id)

    st.markdown("---")
    st.markdown("Made with ❤️ by codemarquis")


main()
