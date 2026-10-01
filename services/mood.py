"""
Typical mood and pace for each genre on a 1–5 scale.

mood: 1 = light & fun … 5 = dark & serious
pace: 1 = slow & thoughtful … 5 = fast & action-packed

This is also the single list of genres the app knows about.
"""
GENRE_PROFILES: dict[str, tuple[int, int]] = {
    "Action": (3, 5),
    "Adventure": (2, 4),
    "Animation": (1, 3),
    "Comedy": (1, 3),
    "Crime": (4, 3),
    "Documentary": (3, 1),
    "Drama": (4, 2),
    "Family": (1, 2),
    "Fantasy": (2, 3),
    "Film-Noir": (5, 2),
    "Horror": (5, 4),
    "Musical": (1, 3),
    "Mystery": (4, 2),
    "Romance": (2, 1),
    "Sci-Fi": (3, 4),
    "Thriller": (4, 4),
    "War": (5, 3),
    "Western": (3, 3),
}


def genres_matching(mood: int, pace: int, tolerance: int = 1) -> set[str]:
    """Genres whose typical mood and pace are both within `tolerance` of the request."""
    return {
        genre
        for genre, (genre_mood, genre_pace) in GENRE_PROFILES.items()
        if abs(genre_mood - mood) <= tolerance and abs(genre_pace - pace) <= tolerance
    }
