"""SEO Meta Injector module for the static-site build system.

Injects canonical URLs, meta descriptions, and Open Graph tags into every
SOP HTML page. The canonical tag is the most important element — it tells
Google which URL to index and prevents duplicate content from both the
old long URL and the new clean URL being indexed simultaneously.

Injected tags (only if not already present):
  <meta name="description" content="...">
  <link rel="canonical" href="https://12thitsop.netlify.app/science/awd/sop1">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="...">
  <meta property="og:description" content="...">
  <meta property="og:url" content="...">
  <meta property="og:type" content="article">
"""

import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Set

from build_system.modules.base import BaseModule
from build_system.utils.fs import scan_files


_SOP_PATTERN = re.compile(r"^([a-z]+)_([a-z]+)_sop(\d+)\.html$", re.IGNORECASE)
_TITLE_RE    = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)

# Tags that indicate SEO is already injected
_CANONICAL_RE = re.compile(r'<link[^>]+rel=["\']canonical["\']', re.IGNORECASE)


def _build_description(title: str, stream: str, subject_code: str, sop_num: int) -> str:
    stream_label = stream.capitalize()
    return (
        f"Std 12th IT {stream_label} Stream SOP {sop_num}: {title.strip()}. "
        f"Skill Oriented Practical for Maharashtra State Board IT subject — {subject_code.upper()}."
    )[:160]


class SeoInjector(BaseModule):
    """Injects canonical, description, and OG tags into SOP HTML files."""

    def run(self) -> bool:
        base_url: str  = self.config.get("SITE_BASE_URL", "").rstrip("/")
        ignored_dirs   = self.config.get("IGNORED_DIRS", set())
        aliases: Dict  = self.config.get("SUBJECT_ALIASES", {})
        skip_files: Set = self.config.get("ASSET_FIXER_SKIP_FILES", set())
        ignored_files  = self.config.get("IGNORED_FILES", set())

        if not base_url:
            print("Error: SITE_BASE_URL not set in config.", file=sys.stderr)
            return False

        all_files = scan_files(self.project_root, ignored_dirs)

        html_files = [
            f for f in all_files
            if f.suffix.lower() == ".html"
            and f.name.lower() not in {s.lower() for s in skip_files}
            and f.name.lower() not in {s.lower() for s in ignored_files}
            and _SOP_PATTERN.match(f.name.lower())
        ]

        injected = 0
        skipped  = 0
        errors   = 0

        for html_path in sorted(html_files, key=str):
            try:
                result = self._process_file(html_path, base_url, aliases)
            except Exception as exc:
                print(f"  ERROR: {html_path.name}: {exc}", file=sys.stderr)
                errors += 1
                continue

            if result is True:
                injected += 1
            else:
                skipped += 1

        print(f"\nSEO tags injected: {injected} files")
        print(f"Already had tags:  {skipped} files (skipped)")
        print(f"Errors:            {errors}")
        return errors == 0

    # ------------------------------------------------------------------

    def _process_file(self, html_path: Path, base_url: str, aliases: Dict) -> bool:
        """Returns True if file was modified, False if skipped."""
        html = html_path.read_text(encoding="utf-8", errors="replace")

        # Skip if canonical already present
        if _CANONICAL_RE.search(html):
            return False

        # Determine stream / subject / sop number
        try:
            rel = html_path.relative_to(self.project_root)
        except ValueError:
            return False
        parts = rel.parts
        if len(parts) != 3:
            return False

        stream         = parts[0].lower()                           # "science"
        subject_folder = parts[1].lower().replace(" ", "-").replace("_", "-")
        alias          = aliases.get(subject_folder, subject_folder)

        m = _SOP_PATTERN.match(html_path.name.lower())
        if not m:
            return False
        sop_num    = int(m.group(3))
        short_path = f"/{stream}/{alias}/sop{sop_num}"
        canon_url  = base_url + short_path

        # Extract existing title
        title_m = _TITLE_RE.search(html)
        title   = title_m.group(1).strip() if title_m else f"SOP {sop_num}"
        desc    = _build_description(title, stream, alias, sop_num)

        seo_block = (
            f'    <meta name="description" content="{desc}">\n'
            f'    <meta name="robots" content="index, follow">\n'
            f'    <link rel="canonical" href="{canon_url}">\n'
            f'    <!-- Open Graph -->\n'
            f'    <meta property="og:type" content="article">\n'
            f'    <meta property="og:title" content="{title}">\n'
            f'    <meta property="og:description" content="{desc}">\n'
            f'    <meta property="og:url" content="{canon_url}">\n'
            f'    <meta property="og:site_name" content="12th IT SOP">\n'
        )

        # Insert before </head>
        head_m = _HEAD_END_RE.search(html)
        if not head_m:
            return False

        # Backup
        bak = html_path.with_suffix(html_path.suffix + ".bak")
        shutil.copy2(html_path, bak)

        new_html = html[: head_m.start()] + seo_block + html[head_m.start():]
        html_path.write_text(new_html, encoding="utf-8")
        return True
