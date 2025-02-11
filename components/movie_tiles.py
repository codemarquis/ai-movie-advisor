import streamlit as st

def display_movie_tiles(movies, cols_per_row=4, section_prefix="main"):
    """
    Display movies in a grid layout with proper styling and image handling
    """
    if not movies:
        st.warning("No movies found.")
        return

    # Create rows of movies
    for i in range(0, len(movies), cols_per_row):
        row_movies = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)

        for col, movie in zip(cols, row_movies):
            with col:
                # Create a container for each movie with consistent height
                with st.container():
                    try:
                        # Display movie poster with error handling
                        poster_url = movie.poster_url if hasattr(movie, 'poster_url') else None
                        if not poster_url:
                            poster_url = f"https://placehold.co/300x450/lightgray/white?text=No+Image"

                        try:
                            st.image(
                                poster_url,
                                use_container_width=True,
                                caption=None
                            )
                        except Exception:
                            fallback_url = f"https://placehold.co/300x450/darkgray/white?text={movie.title.replace(' ', '+')}"
                            st.image(
                                fallback_url,
                                use_container_width=True,
                                caption=None
                            )

                        # Movie title and basic info with custom CSS
                        st.markdown(
                            f"""
                            <div style='text-align: center; padding: 10px;'>
                                <h3 style='margin: 0; font-size: 1.1em; overflow: hidden; 
                                    text-overflow: ellipsis; white-space: nowrap;'>{movie.title}</h3>
                                <p style='margin: 5px 0;'>⭐ {movie.rating:.1f}/5.0</p>
                                <p style='margin: 5px 0;'>🎭 {movie.genre}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Action buttons container
                        button_col1, button_col2 = st.columns(2)
                        with button_col1:
                            if st.button(
                                "➕ Watchlist",
                                key=f"{section_prefix}_add_watchlist_{movie.id}",
                                use_container_width=True,
                                type="secondary"
                            ):
                                if "watchlist" not in st.session_state:
                                    st.session_state.watchlist = set()
                                st.session_state.watchlist.add(movie.id)
                                st.success("Added to watchlist!")

                        with button_col2:
                            if st.button(
                                "📖 Details",
                                key=f"{section_prefix}_show_details_{movie.id}",
                                use_container_width=True,
                                type="primary"
                            ):
                                with st.expander(f"Details for {movie.title}", expanded=True):
                                    st.markdown(f"""
                                    ### {movie.title} ({movie.year})
                                    **Genre:** {movie.genre}
                                    **Rating:** ⭐ {movie.rating}/5.0
                                    **Votes:** {movie.votes:,}

                                    {getattr(movie, 'overview', 'No overview available.')}
                                    """)
                    except Exception as e:
                        st.error(f"Error displaying movie: {str(e)}")

def display_watchlist(movies_dict):
    """Display watchlist movies with proper error handling"""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = set()

    watchlist_movies = [
        movie for movie in movies_dict.values()
        if movie.id in st.session_state.watchlist
    ]

    if not watchlist_movies:
        st.info("Your watchlist is empty. Add movies by clicking the '+' button!")
        return

    display_movie_tiles(watchlist_movies, section_prefix="watchlist")