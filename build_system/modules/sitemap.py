"""Sitemap generator module skeleton.

This module will be responsible for generating sitemap.xml.
"""

from build_system.modules.base import BaseModule


class SitemapGenerator(BaseModule):
    """Generates sitemap.xml for the static site."""

    def run(self) -> bool:
        """Executes sitemap generation.

        Returns:
            bool: True if completed successfully, False otherwise.
        """
        print("Sitemap generator is not implemented yet. Skipping.")
        return True
