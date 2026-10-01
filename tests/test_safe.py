from components.movie_tiles import caption_html
from components.safe import PLACEHOLDER_POSTER, escape_html, escape_markdown, safe_poster
from models.domain import Movie


def test_escape_html_neutralises_tags_and_quotes():
    assert escape_html('<img src=x onerror="a()">') == "&lt;img src=x onerror=&quot;a()&quot;&gt;"


def test_escape_markdown_neutralises_links_and_emphasis():
    escaped = escape_markdown("[click](https://evil.example) *bold* <b>")
    assert "[" not in escaped.replace("\\[", "")
    assert escaped.startswith("\\[click\\]\\(https://evil\\.example\\)")


def test_safe_poster_only_allows_https():
    assert safe_poster("https://upload.wikimedia.org/a.jpg") == "https://upload.wikimedia.org/a.jpg"
    for bad in ("javascript:alert(1)", "http://insecure.example/a.jpg", "data:image/png;base64,AAA", None, 42):
        assert safe_poster(bad) == PLACEHOLDER_POSTER


def test_tile_caption_escapes_untrusted_title_and_genre():
    movie = Movie(1, "<script>x</script>", "<b>Drama</b>", 2000, 4.25, 10, None)
    html = caption_html(movie)
    assert "<script>" not in html and "<b>" not in html
    assert "&lt;script&gt;" in html and "4.2/5" in html
