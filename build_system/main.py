"""Main execution script for the Static Site Build System.

Run from the project root:

    python build_system/main.py [--root PATH] [--skip-asset-fix] [--skip-sitemap] [--skip-seo]

Modules executed in order:
    1. RedirectsGenerator  — _redirects (301!/200 rules for all SOP pages)
    2. AssetFixer          — rewrites relative asset paths to root-relative
    3. SitemapGenerator    — sitemap.xml with all clean canonical URLs
    4. RobotsGenerator     — robots.txt pointing to sitemap
    5. SeoInjector         — canonical, description, and Open Graph tags in HTML
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_system.config import (
    SUBJECT_ALIASES,
    IGNORED_DIRS,
    IGNORED_FILES,
    ASSET_FIXER_SKIP_FILES,
    SITE_BASE_URL,
)
from build_system.modules.redirects import RedirectsGenerator
from build_system.modules.asset_fixer import AssetFixer
from build_system.modules.sitemap import SitemapGenerator
from build_system.modules.robots import RobotsGenerator
from build_system.modules.seo import SeoInjector


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Static Site Build System — redirects, assets, sitemap, robots, SEO.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-r", "--root", type=str, default=".",
                        help="Path to the website project root (default: current directory).")
    parser.add_argument("--skip-asset-fix", action="store_true", default=False,
                        help="Skip the HTML asset path rewriting step.")
    parser.add_argument("--skip-sitemap", action="store_true", default=False,
                        help="Skip sitemap.xml generation.")
    parser.add_argument("--skip-seo", action="store_true", default=False,
                        help="Skip SEO meta tag injection.")

    args = parser.parse_args()
    project_root = Path(args.root).resolve()

    if not project_root.exists():
        print(f"Error: Project root '{project_root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    config: Dict[str, Any] = {
        "SUBJECT_ALIASES":        SUBJECT_ALIASES,
        "IGNORED_DIRS":           IGNORED_DIRS,
        "IGNORED_FILES":          IGNORED_FILES,
        "ASSET_FIXER_SKIP_FILES": ASSET_FIXER_SKIP_FILES,
        "SITE_BASE_URL":          SITE_BASE_URL,
    }

    def run_module(label: str, module_instance) -> None:
        print()
        print("=" * 60)
        print(f"MODULE — {label}")
        print("=" * 60)
        ok = module_instance.run()
        if not ok:
            print(f"{label} failed. Aborting.", file=sys.stderr)
            sys.exit(1)

    run_module("Redirect Generator",  RedirectsGenerator(project_root, config))

    if not args.skip_asset_fix:
        run_module("Asset Path Fixer",    AssetFixer(project_root, config))
    else:
        print("\n[Asset path fixer skipped via --skip-asset-fix]")

    if not args.skip_sitemap:
        run_module("Sitemap Generator",   SitemapGenerator(project_root, config))
        run_module("Robots.txt Generator", RobotsGenerator(project_root, config))
    else:
        print("\n[Sitemap + robots skipped via --skip-sitemap]")

    if not args.skip_seo:
        run_module("SEO Meta Injector",   SeoInjector(project_root, config))
    else:
        print("\n[SEO tag injection skipped via --skip-seo]")

    print()
    print("=" * 60)
    print("All modules completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
