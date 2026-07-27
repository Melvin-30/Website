"""Asset Path Fixer module for the static-site build system.

Converts every relative asset reference in SOP HTML files to a root-relative
path so that Netlify can serve them correctly regardless of which URL the
browser uses to reach the page.

Example transformation:
    href="SOP page Style.css"
    →  href="/Science/JavaScript/SOP page Style.css"
"""

import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Set

from build_system.modules.base import BaseModule
from build_system.utils.fs import scan_files
from build_system.utils.html_parser import iter_asset_refs, is_relative


# ---------------------------------------------------------------------------
# Asset category classification (for reporting)
# ---------------------------------------------------------------------------
_CSS_TAGS = {"link"}
_SCRIPT_TAGS = {"script"}
_IMAGE_TAGS = {"img", "use", "input", "picture"}
_AUDIO_TAGS = {"audio"}
_VIDEO_TAGS = {"video", "source"}   # <source> inside <video> counts as video
_IFRAME_TAGS = {"iframe"}
_OBJECT_TAGS = {"object", "embed"}

_EXT_AUDIO = {".mp3", ".ogg", ".wav", ".flac", ".aac", ".m4a", ".opus"}
_EXT_VIDEO = {".mp4", ".webm", ".ogv", ".avi", ".mov", ".m4v"}
_EXT_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".avif", ".ico", ".bmp"}
_EXT_FONT  = {".woff", ".woff2", ".ttf", ".otf", ".eot"}
_EXT_PDF   = {".pdf"}


def _categorise(tag: str, attr: str, value: str) -> str:
    """Return a human-readable category name for the asset reference."""
    ext = Path(value.split("?")[0]).suffix.lower()
    if tag in _CSS_TAGS or ext == ".css":
        return "css"
    if tag in _SCRIPT_TAGS or ext == ".js":
        return "scripts"
    if ext in _EXT_AUDIO:
        return "audio"
    if ext in _EXT_VIDEO or tag in _VIDEO_TAGS and attr == "src":
        return "video"
    if ext in _EXT_FONT:
        return "fonts"
    if ext in _EXT_PDF:
        return "pdfs"
    if ext in _EXT_IMAGE or tag in _IMAGE_TAGS:
        return "images"
    return "other"


class AssetFixer(BaseModule):
    """Rewrites relative asset references in HTML to root-relative paths."""

    def run(self) -> bool:
        """Execute asset path correction across all discovered HTML files.

        Returns:
            bool: True if completed with no fatal errors.
        """
        ignored_dirs: Set[str] = self.config.get("IGNORED_DIRS", set())
        skip_files: Set[str]   = self.config.get("ASSET_FIXER_SKIP_FILES", set())

        all_files = scan_files(self.project_root, ignored_dirs)

        html_files = [
            f for f in all_files
            if f.suffix.lower() == ".html"
            and f.name not in {s.lower() for s in skip_files}
            and not any(p.lower() in {"images", "fonts", "scripts", "css", "js"}
                        for p in f.parts)
        ]

        # Counters
        files_processed = 0
        files_skipped   = 0
        errors          = 0
        counts: Dict[str, int] = defaultdict(int)

        for html_path in html_files:
            try:
                result = self._process_file(html_path, skip_files)
            except Exception as exc:
                print(f"  ERROR processing {html_path.relative_to(self.project_root)}: {exc}",
                      file=sys.stderr)
                errors += 1
                continue

            if result is None:
                files_skipped += 1
                continue

            changed, file_counts = result
            if changed:
                files_processed += 1
                for cat, n in file_counts.items():
                    counts[cat] += n
            else:
                files_skipped += 1

        # Print summary
        print(f"\nHTML files processed:  {files_processed}")
        print(f"HTML files skipped:    {files_skipped}")
        print()
        if counts.get("css"):
            print(f"CSS links updated:     {counts['css']}")
        if counts.get("images"):
            print(f"Images updated:        {counts['images']}")
        if counts.get("scripts"):
            print(f"Scripts updated:       {counts['scripts']}")
        if counts.get("audio"):
            print(f"Audio updated:         {counts['audio']}")
        if counts.get("video"):
            print(f"Video updated:         {counts['video']}")
        if counts.get("fonts"):
            print(f"Fonts updated:         {counts['fonts']}")
        if counts.get("pdfs"):
            print(f"PDFs updated:          {counts['pdfs']}")
        if counts.get("other"):
            print(f"Other assets updated:  {counts['other']}")
        print(f"\nErrors:                {errors}")

        return errors == 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_file(
        self,
        html_path: Path,
        skip_files: Set[str],
    ):
        """Process a single HTML file.

        Returns:
            None if the file was skipped (no relative refs or in skip list).
            (changed: bool, counts: dict) otherwise.
        """
        # Skip files by name (case-insensitive)
        if html_path.name.lower() in {s.lower() for s in skip_files}:
            return None

        # The root-relative prefix is /{stream_folder}/{subject_folder}
        # i.e. the two path components above the file (depth 2 below project root)
        try:
            rel = html_path.relative_to(self.project_root)
        except ValueError:
            return None

        parts = rel.parts
        if len(parts) != 3:
            # Not a Stream/Subject/file.html layout — skip silently
            return None

        stream_folder  = parts[0]   # e.g. "Science"
        subject_folder = parts[1]   # e.g. "JavaScript"
        url_prefix     = f"/{stream_folder}/{subject_folder}"

        html_text = html_path.read_text(encoding="utf-8", errors="replace")

        refs = list(iter_asset_refs(html_text))
        relative_refs = [r for r in refs if is_relative(r.value)]

        if not relative_refs:
            return False, {}

        # Backup before any modification
        bak_path = html_path.with_suffix(html_path.suffix + ".bak")
        shutil.copy2(html_path, bak_path)

        # Rewrite right-to-left so character positions stay valid
        relative_refs_sorted = sorted(relative_refs, key=lambda r: r.val_start, reverse=True)

        new_html = html_text
        file_counts: Dict[str, int] = defaultdict(int)
        changed = False

        for ref in relative_refs_sorted:
            original_value = ref.value
            # Build the root-relative replacement — preserve the filename exactly
            new_value = f"{url_prefix}/{original_value}"

            # Replace in the string using exact character positions
            new_html = (
                new_html[: ref.val_start]
                + new_value
                + new_html[ref.val_end :]
            )
            cat = _categorise(ref.tag, ref.attr, original_value)
            file_counts[cat] += 1
            changed = True

        if changed:
            html_path.write_text(new_html, encoding="utf-8")

        return changed, dict(file_counts)
