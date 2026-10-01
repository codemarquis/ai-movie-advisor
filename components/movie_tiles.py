import streamlit as st

from components.safe import escape_html, safe_poster
from models.domain import Movie

TILE_CSS = """
<style>
.ama-tile { text-align: center; padding: 8px 4px 4px; }
.ama-title { margin: 0; font-size: 1.05em; font-weight: 600;
             overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ama-meta { margin: 4px 0 0; opacity: 0.85; }
</style>
"""


def _toggle_watchlist(movie_id: int) -> None:
    watchlist: set[int] = st.session_state.setdefault("watchlist", set())
    watchlist.symmetric_difference_update({movie_id})


def _open_details(movie_id: int) -> None:
    st.session_state["details_id"] = movie_id


def caption_html(movie: Movie) -> str:
    """Tile caption. Every value is escaped: titles and genres are untrusted data."""
    title = escape_html(movie.title)
    return (
        f"<div class='ama-tile'><p class='ama-title' title='{title}'>{title}</p>"
        f"<p class='ama-meta'>⭐ {movie.rating:.1f}/5 · {movie.year}</p>"
        f"<p class='ama-meta'>🎭 {escape_html(movie.genre)}</p></div>"
    )


def display_movie_tiles(movies: list[Movie], section: str, watchlist: set[int], per_row: int = 4) -> None:
    for start in range(0, len(movies), per_row):
        columns = st.columns(per_row)
        for column, movie in zip(columns, movies[start:start + per_row], strict=False):
            with column, st.container():
                st.image(safe_poster(movie.poster_url), width="stretch")
                st.markdown(caption_html(movie), unsafe_allow_html=True)
                saved = movie.id in watchlist
                add_col, info_col = st.columns(2)
                add_col.button(
                    "✓ Saved" if saved else "➕ Watchlist",
                    key=f"{section}_watch_{movie.id}",
                    on_click=_toggle_watchlist,
                    args=(movie.id,),
                    help="Remove from watchlist" if saved else "Add to watchlist",
                    width="stretch",
                )
                info_col.button(
                    "📖 Details",
                    key=f"{section}_details_{movie.id}",
                    on_click=_open_details,
                    args=(movie.id,),
                    type="primary",
                    width="stretch",
                )
