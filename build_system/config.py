"""Configuration settings for the Static Site Build System.

This module houses the configuration settings, path ignores, and editable
subject aliases used by the build modules.
"""

from typing import Dict, Set

# ---------------------------------------------------------------------------
# Subject folder alias mapping
# Normalised folder name (lowercase, underscores → dashes) → short code.
# If a folder name is not listed here the normalised folder name is used as-is.
# ---------------------------------------------------------------------------
SUBJECT_ALIASES: Dict[str, str] = {
    # Science
    "advanced-web-designing": "awd",
    "web-designing": "wd",
    "information-technology": "it",
    "database-management": "dbms",
    "java-programming": "java",
    "python-programming": "python",
    "javascript": "js",

    # Commerce
    "digital-marketing": "dm",
    "computerised-accounting": "ca",
    "database-concept": "dc",
}

# ---------------------------------------------------------------------------
# Directory names to skip completely during recursive scanning
# ---------------------------------------------------------------------------
IGNORED_DIRS: Set[str] = {
    "assets",
    "css",
    "js",
    "images",
    "fonts",
    "scripts",
    "node_modules",
    ".git",
    ".github",
    "build_system",   # Never scan the build system itself
    "__pycache__",
}

# ---------------------------------------------------------------------------
# Specific filenames to ignore during SOP detection
# ---------------------------------------------------------------------------
IGNORED_FILES: Set[str] = {
    "index.html",
    "404.html",
}

# ---------------------------------------------------------------------------
# HTML files excluded from asset path rewriting
# (they already use root-level paths and/or must not be altered)
# ---------------------------------------------------------------------------
ASSET_FIXER_SKIP_FILES: Set[str] = {
    "404.html",
    "coming_soon.html",
    "Index.html",
    "Formating.html",
}
