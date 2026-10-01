"""
Output encoding for anything that came from the database or an external API.

Zero trust: titles, genres and URLs are data, never markup. Everything shown
through st.markdown goes through these helpers first.
"""
import html
import re

PLACEHOLDER_POSTER = "https://placehold.co/300x450/1f2937/e5e7eb?text=No+poster"

_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>~$])")


def escape_html(text: object) -> str:
    return html.escape(str(text), quote=True)


def escape_markdown(text: object) -> str:
    """Backslash-escape Markdown syntax so text renders literally (no links, images, HTML)."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", str(text))


def safe_poster(url: object) -> str:
    return url if isinstance(url, str) and url.startswith("https://") else PLACEHOLDER_POSTER
