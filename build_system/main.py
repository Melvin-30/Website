"""Main execution script for the Static Site Build System.

Run from the project root:

    python build_system/main.py [--root PATH] [--skip-asset-fix]

Modules executed in order:
    1. RedirectsGenerator  — generates _redirects with dual 301 + 200 rules
    2. AssetFixer          — rewrites relative asset paths to root-relative form
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure the project root is in sys.path so package imports work when the
# script is invoked directly (e.g. python build_system/main.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_system.config import (
    SUBJECT_ALIASES,
    IGNORED_DIRS,
    IGNORED_FILES,
    ASSET_FIXER_SKIP_FILES,
)
from build_system.modules.redirects import RedirectsGenerator
from build_system.modules.asset_fixer import AssetFixer


def main() -> None:
    """Parse CLI arguments and run active builder modules."""
    parser = argparse.ArgumentParser(
        description="Static Site Build System — generates _redirects and fixes asset paths.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r", "--root",
        type=str,
        default=".",
        help="Path to the website project root directory (default: current directory).",
    )
    parser.add_argument(
        "--skip-asset-fix",
        action="store_true",
        default=False,
        help="Skip the HTML asset path rewriting step.",
    )

    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    if not project_root.exists():
        print(f"Error: Project root '{project_root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    config: Dict[str, Any] = {
        "SUBJECT_ALIASES":       SUBJECT_ALIASES,
        "IGNORED_DIRS":          IGNORED_DIRS,
        "IGNORED_FILES":         IGNORED_FILES,
        "ASSET_FIXER_SKIP_FILES": ASSET_FIXER_SKIP_FILES,
    }

    # ------------------------------------------------------------------
    # Module 1: Redirect rules
    # ------------------------------------------------------------------
    print("=" * 60)
    print("MODULE 1 — Redirect Generator")
    print("=" * 60)
    redirects_ok = RedirectsGenerator(project_root, config).run()

    if not redirects_ok:
        print("Redirect generation failed. Aborting.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Module 2: Asset path fixer
    # ------------------------------------------------------------------
    if not args.skip_asset_fix:
        print()
        print("=" * 60)
        print("MODULE 2 — Asset Path Fixer")
        print("=" * 60)
        asset_ok = AssetFixer(project_root, config).run()
        if not asset_ok:
            print("Asset fixer encountered errors (see above).", file=sys.stderr)
            sys.exit(1)
    else:
        print("\n[Asset path fixer skipped via --skip-asset-fix]")


if __name__ == "__main__":
    main()
