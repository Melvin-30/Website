"""HTML asset reference parser for the static-site build system.

Uses the standard-library html.parser — no third-party dependencies.
Yields every asset reference found in an HTML string so the caller can
decide how (and whether) to rewrite them.
"""

from html.parser import HTMLParser
from dataclasses import dataclass
from typing import Iterator, Optional


# ---------------------------------------------------------------------------
# Mapping: tag name → attribute name that holds the asset URL.
# Tags with multiple potential asset attrs are listed in priority order;
# only the first matching attr found on a given element is yielded.
# ---------------------------------------------------------------------------
_TAG_ATTR_MAP: dict[str, list[str]] = {
    "link":   ["href"],
    "script": ["src"],
    "img":    ["src"],
    "audio":  ["src"],
    "video":  ["src"],
    "source": ["src", "srcset"],
    "iframe": ["src"],
    "embed":  ["src"],
    "input":  ["src"],          # <input type="image">
    "object": ["data"],
    "use":    ["href", "xlink:href"],
}

# link[rel] values that carry asset URLs (stylesheets, favicons, etc.)
_LINK_ASSET_RELS = {
    "stylesheet",
    "icon",
    "shortcut icon",
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
    "manifest",
    "preload",
    "prefetch",
}

# URL schemes / prefixes that must never be rewritten
_SKIP_PREFIXES = (
    "http://",
    "https://",
    "//",
    "mailto:",
    "tel:",
    "data:",
    "javascript:",
    "#",
)


@dataclass
class AssetRef:
    """Represents a single asset reference found in an HTML document."""
    tag: str            # e.g. "img"
    attr: str           # e.g. "src"
    value: str          # original attribute value
    # Character positions inside the raw HTML string
    val_start: int      # index of opening quote + 1
    val_end: int        # index of closing quote


def is_relative(url: str) -> bool:
    """Return True if *url* is a relative path that should be rewritten."""
    if not url or not url.strip():
        return False
    return not url.startswith(_SKIP_PREFIXES) and not url.startswith("/")


class _AssetParser(HTMLParser):
    """Internal parser that records every asset reference with its position."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=False)
        self._html = html
        self.refs: list[AssetRef] = []

    # ------------------------------------------------------------------
    # HTMLParser hook
    # ------------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        attr_map = dict(attrs)  # attr-name → value (both lowercased by HTMLParser)

        target_attrs = _TAG_ATTR_MAP.get(tag)
        if not target_attrs:
            return

        # Special rule: <link> tags are only asset carriers for certain rel values
        if tag == "link":
            rel = attr_map.get("rel", "").strip().lower()
            if rel not in _LINK_ASSET_RELS:
                return

        for attr_name in target_attrs:
            raw_value = attr_map.get(attr_name)
            if raw_value is None:
                continue
            if not raw_value.strip():
                continue

            # Handle srcset (comma-separated list of "url [descriptor]" entries)
            if attr_name == "srcset":
                self._record_srcset(tag, attr_name, raw_value)
            else:
                self._record_single(tag, attr_name, raw_value)
            break  # only process the first matching attr per element

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _record_single(self, tag: str, attr: str, value: str) -> None:
        """Find the byte position of *value* inside the raw HTML and record it."""
        start = self.getpos()          # (line, col) — 1-indexed
        pos = self._find_attr_value(value)
        if pos is not None:
            val_start, val_end = pos
            self.refs.append(AssetRef(tag, attr, value, val_start, val_end))

    def _record_srcset(self, tag: str, attr: str, value: str) -> None:
        """Parse a srcset string and record each individual URL."""
        for entry in value.split(","):
            parts = entry.strip().split()
            if not parts:
                continue
            url = parts[0]
            pos = self._find_attr_value(url)
            if pos is not None:
                val_start, val_end = pos
                self.refs.append(AssetRef(tag, attr, url, val_start, val_end))

    def _find_attr_value(self, value: str) -> Optional[tuple[int, int]]:
        """
        Search forward from the current parse position for *value* as an
        attribute value (surrounded by quotes or the end of the attribute).
        Returns (start, end) character indices into self._html, or None.
        """
        # getpos() gives us (line, col) in 1-indexed form.
        line_no, col = self.getpos()
        # Convert to absolute character offset
        lines = self._html.splitlines(keepends=True)
        offset = sum(len(l) for l in lines[:line_no - 1]) + col - 1

        # Search within the next 1 024 characters to stay fast
        window = self._html[offset: offset + 4096]
        idx = window.find(value)
        if idx == -1:
            return None
        abs_start = offset + idx
        return abs_start, abs_start + len(value)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def iter_asset_refs(html: str) -> Iterator[AssetRef]:
    """Parse *html* and yield every asset reference as an :class:`AssetRef`.

    Only relative URLs are yielded; externals and root-relative paths are
    filtered out by the caller (or you can call :func:`is_relative` yourself).

    Args:
        html: Raw HTML string to parse.

    Yields:
        :class:`AssetRef` for every asset attribute encountered.
    """
    parser = _AssetParser(html)
    try:
        parser.feed(html)
    except Exception:
        # If the parser blows up we still return whatever was collected
        pass
    yield from parser.refs
