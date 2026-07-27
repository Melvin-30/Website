"""Robots.txt generator module for the static-site build system.

Generates robots.txt in the project root, allowing all crawlers and
pointing to the sitemap for indexing.
"""

import sys
from build_system.modules.base import BaseModule


class RobotsGenerator(BaseModule):
    """Generates robots.txt pointing to the sitemap."""

    def run(self) -> bool:
        base_url: str = self.config.get("SITE_BASE_URL", "").rstrip("/")
        if not base_url:
            print("Error: SITE_BASE_URL not set in config.", file=sys.stderr)
            return False

        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            f"Sitemap: {base_url}/sitemap.xml\n"
        )

        robots_path = self.project_root / "robots.txt"
        try:
            robots_path.write_text(content, encoding="utf-8")
        except OSError as e:
            print(f"Error writing robots.txt: {e}", file=sys.stderr)
            return False

        print("robots.txt generated")
        return True
