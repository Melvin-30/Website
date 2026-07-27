"""Sitemap generator module for the static-site build system.

Generates a standards-compliant sitemap.xml in the project root containing:
  - The homepage
  - All SOP pages (using their clean short URLs)
  - The coming-soon page

Google Search Console requires the sitemap to use canonical URLs only.
"""

import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

from build_system.modules.base import BaseModule
from build_system.utils.fs import scan_files, normalize_name


_SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
_SOP_PATTERN = r"^([a-z]+)_([a-z]+)_sop(\d+)\.html$"

import re


class SitemapGenerator(BaseModule):
    """Generates sitemap.xml with all canonical clean URLs."""

    def run(self) -> bool:
        base_url: str = self.config.get("SITE_BASE_URL", "").rstrip("/")
        ignored_dirs = self.config.get("IGNORED_DIRS", set())
        aliases: Dict[str, str] = self.config.get("SUBJECT_ALIASES", {})
        ignored_files = self.config.get("IGNORED_FILES", set())
        today = date.today().isoformat()

        if not base_url:
            print("Error: SITE_BASE_URL not set in config.", file=sys.stderr)
            return False

        # ---------------------------------------------------------------
        # Discover all SOP short URLs (same logic as redirects module)
        # ---------------------------------------------------------------
        all_files = scan_files(self.project_root, ignored_dirs)
        urls: List[Dict[str, str]] = []

        # Homepage
        urls.append({
            "loc": base_url + "/",
            "changefreq": "weekly",
            "priority": "1.0",
            "lastmod": today,
        })

        sop_pattern = re.compile(_SOP_PATTERN, re.IGNORECASE)

        seen_short_urls = set()
        sop_urls = []

        for f in sorted(all_files, key=lambda p: str(p)):
            if f.name.lower() in {fn.lower() for fn in ignored_files}:
                continue
            if not f.name.lower().endswith(".html"):
                continue
            if not sop_pattern.match(f.name.lower()):
                continue

            # Determine stream and subject
            try:
                rel = f.relative_to(self.project_root)
            except ValueError:
                continue
            parts = rel.parts
            if len(parts) != 3:
                continue

            stream = parts[0].lower()           # "science"
            subject_folder = parts[1].lower().replace(" ", "-").replace("_", "-")
            alias = aliases.get(subject_folder, subject_folder)

            m = sop_pattern.match(f.name.lower())
            if not m:
                continue
            sop_num = int(m.group(3))
            short_url = f"/{stream}/{alias}/sop{sop_num}"

            if short_url in seen_short_urls:
                continue
            seen_short_urls.add(short_url)

            sop_urls.append({
                "loc": base_url + short_url,
                "changefreq": "monthly",
                "priority": "0.8",
                "lastmod": today,
            })

        urls.extend(sop_urls)

        # ---------------------------------------------------------------
        # Build XML
        # ---------------------------------------------------------------
        ET.register_namespace("", _SITEMAP_NS)
        root = ET.Element(f"{{{_SITEMAP_NS}}}urlset")

        for entry in urls:
            url_el = ET.SubElement(root, f"{{{_SITEMAP_NS}}}url")
            ET.SubElement(url_el, f"{{{_SITEMAP_NS}}}loc").text = entry["loc"]
            ET.SubElement(url_el, f"{{{_SITEMAP_NS}}}lastmod").text = entry["lastmod"]
            ET.SubElement(url_el, f"{{{_SITEMAP_NS}}}changefreq").text = entry["changefreq"]
            ET.SubElement(url_el, f"{{{_SITEMAP_NS}}}priority").text = entry["priority"]

        # Indent for readability (Python 3.9+)
        try:
            ET.indent(root, space="  ")
        except AttributeError:
            pass

        tree = ET.ElementTree(root)
        sitemap_path = self.project_root / "sitemap.xml"
        try:
            with open(sitemap_path, "w", encoding="utf-8", newline="\n") as f_out:
                f_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                tree.write(f_out, encoding="unicode", xml_declaration=False)
                f_out.write("\n")
        except OSError as e:
            print(f"Error writing sitemap.xml: {e}", file=sys.stderr)
            return False

        print(f"sitemap.xml generated: {len(urls)} URLs")
        print(f"  Homepage:   1")
        print(f"  SOP pages:  {len(sop_urls)}")
        return True
