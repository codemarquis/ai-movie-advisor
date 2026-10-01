import streamlit as st
import plotly.graph_objects as go

def display_movie_card(movie):
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(movie.poster_url, use_container_width=True)

    with col2:
        st.header(movie.title)
        st.write(f"**Genre:** {movie.genre}")
        st.write(f"**Year:** {movie.year}")
        st.write(f"**Rating:** {movie.rating:.1f}/5.0")
        st.write(f"**Votes:** {movie.votes:,}")

        # Add rating input
        user_rating = st.slider(
            "Rate this movie",
            1.0, 5.0, 3.0, 0.5,
            key=f"rating_{movie.id}"
        )

def plot_rating_distribution(ratings):
    fig = go.Figure(data=[
        go.Histogram(x=ratings, nbinsx=10)
    ])

    fig.update_layout(
        title="Rating Distribution",
        xaxis_title="Rating",
        yaxis_title="Count",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)